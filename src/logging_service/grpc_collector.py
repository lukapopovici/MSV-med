"""
gRPC Server for receiving OTLP spans.

This service implements the OpenTelemetry Protocol (OTLP) gRPC endpoint
to receive spans directly from OpenTelemetry SDKs.

File location: app/services/grpc_collector.py

Installation requirements:
    pip install grpcio grpcio-tools opentelemetry-proto pymongo pydantic
"""
import os
import logging
from concurrent import futures
from datetime import datetime

import grpc
from pymongo import MongoClient

# Import OTLP protobuf definitions
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc
from opentelemetry.proto.trace.v1 import trace_pb2
from opentelemetry.proto.common.v1 import common_pb2

# Import our models - THIS IS THE KEY IMPORT
from models.span_models import SpanEventDTO, SpanLinkDTO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "telemetry")


class TraceServiceServicer(trace_service_pb2_grpc.TraceServiceServicer):
    """Implements the OTLP TraceService gRPC endpoint."""
    
    def __init__(self):
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client[DATABASE_NAME]
        self.spans_collection = self.db["spans"]
        
        # Ensure indexes
        self.spans_collection.create_index([("trace_id", 1), ("start_time", -1)])
        self.spans_collection.create_index([("service_name", 1), ("start_time", -1)])
        self.spans_collection.create_index([("span_id", 1)])
        
        logger.info("TraceService initialized with MongoDB")
    
    def Export(self, request, context):
        """
        Receives OTLP trace export requests and stores spans in MongoDB.
        
        Args:
            request: ExportTraceServiceRequest containing resource spans
            context: gRPC context
            
        Returns:
            ExportTraceServiceResponse
        """
        try:
            spans_processed = 0
            
            for resource_span in request.resource_spans:
                # Extract resource attributes
                resource_attributes = self._extract_attributes(
                    resource_span.resource.attributes
                )
                
                # Get service name from resource attributes
                service_name = resource_attributes.get(
                    "service.name", 
                    "unknown-service"
                )
                
                for scope_span in resource_span.scope_spans:
                    for span in scope_span.spans:
                        try:
                            self._store_span(
                                span, 
                                service_name, 
                                resource_attributes
                            )
                            spans_processed += 1
                        except Exception as e:
                            logger.error(f"Error storing span: {e}", exc_info=True)
            
            logger.info(f"Processed {spans_processed} spans")
            
            return trace_service_pb2.ExportTraceServiceResponse(
                partial_success=trace_service_pb2.ExportTracePartialSuccess(
                    rejected_spans=0,
                    error_message=""
                )
            )
            
        except Exception as e:
            logger.error(f"Error in Export: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return trace_service_pb2.ExportTraceServiceResponse()
    
    def _store_span(self, span, service_name: str, resource_attributes: dict):
        """Store a single span in MongoDB."""
        
        # Convert trace_id and span_id from bytes to hex string
        trace_id = span.trace_id.hex()
        span_id = span.span_id.hex()
        parent_span_id = span.parent_span_id.hex() if span.parent_span_id else None
        
        # Convert nanosecond timestamps to datetime
        start_time = datetime.fromtimestamp(span.start_time_unix_nano / 1e9)
        end_time = datetime.fromtimestamp(span.end_time_unix_nano / 1e9) if span.end_time_unix_nano else None
        
        # Calculate duration in milliseconds
        duration_ms = None
        if end_time:
            duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Extract attributes
        attributes = self._extract_attributes(span.attributes)
        
        # Extract events
        events = []
        for event in span.events:
            events.append({
                "name": event.name,
                "timestamp": datetime.fromtimestamp(event.time_unix_nano / 1e9),
                "attributes": self._extract_attributes(event.attributes)
            })
        
        # Extract links
        links = []
        for link in span.links:
            links.append({
                "trace_id": link.trace_id.hex(),
                "span_id": link.span_id.hex(),
                "attributes": self._extract_attributes(link.attributes)
            })
        
        # Map span kind
        kind_mapping = {
            trace_pb2.Span.SPAN_KIND_UNSPECIFIED: "UNSPECIFIED",
            trace_pb2.Span.SPAN_KIND_INTERNAL: "INTERNAL",
            trace_pb2.Span.SPAN_KIND_SERVER: "SERVER",
            trace_pb2.Span.SPAN_KIND_CLIENT: "CLIENT",
            trace_pb2.Span.SPAN_KIND_PRODUCER: "PRODUCER",
            trace_pb2.Span.SPAN_KIND_CONSUMER: "CONSUMER",
        }
        kind = kind_mapping.get(span.kind, "UNSPECIFIED")
        
        # Map status code
        status_code_mapping = {
            trace_pb2.Status.STATUS_CODE_UNSET: "UNSET",
            trace_pb2.Status.STATUS_CODE_OK: "OK",
            trace_pb2.Status.STATUS_CODE_ERROR: "ERROR",
        }
        status_code = status_code_mapping.get(span.status.code, "UNSET")
        
        # Create span document
        span_doc = {
            "_id": f"{trace_id}_{span_id}",
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "name": span.name,
            "kind": kind,
            "status_code": status_code,
            "status_message": span.status.message if span.status.message else None,
            "start_time": start_time,
            "end_time": end_time,
            "duration_ms": duration_ms,
            "service_name": service_name,
            "attributes": attributes,
            "resource_attributes": resource_attributes,
            "events": events if events else None,
            "links": links if links else None,
            "received_at": datetime.utcnow()
        }
        
        # Insert or update span
        self.spans_collection.replace_one(
            {"_id": span_doc["_id"]},
            span_doc,
            upsert=True
        )
        
        logger.debug(f"Stored span: {span.name} (trace={trace_id[:8]}...)")
    
    def _extract_attributes(self, attributes):
        """Extract attributes from OTLP KeyValue list."""
        result = {}
        
        for kv in attributes:
            key = kv.key
            value = kv.value
            
            # Extract value based on type
            if value.HasField('string_value'):
                result[key] = value.string_value
            elif value.HasField('bool_value'):
                result[key] = value.bool_value
            elif value.HasField('int_value'):
                result[key] = value.int_value
            elif value.HasField('double_value'):
                result[key] = value.double_value
            elif value.HasField('array_value'):
                result[key] = [self._extract_any_value(v) for v in value.array_value.values]
            elif value.HasField('kvlist_value'):
                result[key] = self._extract_attributes(value.kvlist_value.values)
        
        return result
    
    def _extract_any_value(self, value):
        """Extract a single AnyValue."""
        if value.HasField('string_value'):
            return value.string_value
        elif value.HasField('bool_value'):
            return value.bool_value
        elif value.HasField('int_value'):
            return value.int_value
        elif value.HasField('double_value'):
            return value.double_value
        elif value.HasField('array_value'):
            return [self._extract_any_value(v) for v in value.array_value.values]
        elif value.HasField('kvlist_value'):
            return self._extract_attributes(value.kvlist_value.values)
        return None


def serve():
    """Start the gRPC server."""
    port = os.getenv("GRPC_PORT", "4317")
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    trace_service_pb2_grpc.add_TraceServiceServicer_to_server(
        TraceServiceServicer(), 
        server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logger.info(f"gRPC Span Collector listening on port {port}")
    logger.info("Ready to receive OTLP spans...")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(0)


if __name__ == '__main__':
    serve()