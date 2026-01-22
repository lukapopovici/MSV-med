"""
OpenTelemetry Span Collector Service - REST API

This service provides a REST API for querying spans stored in MongoDB.

File location: app/services/rest_api.py

Installation requirements:
    pip install fastapi uvicorn pymongo pydantic python-dotenv
"""
import os
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient

# Import our models - THIS IS THE KEY IMPORT
from models.span_models import (
    SpanCreateDTO, SpanResponseDTO, 
    TraceResponseDTO, SpanEventDTO, SpanLinkDTO
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "telemetry")

# Global MongoDB client
mongo_client: Optional[MongoClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, cleanup on shutdown."""
    global mongo_client
    
    # Initialize MongoDB connection
    logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
    mongo_client = MongoClient(MONGODB_URI)
    
    db = mongo_client[DATABASE_NAME]
    spans_collection = db["spans"]
    
    # Ensure indexes exist
    spans_collection.create_index([("trace_id", 1), ("start_time", -1)])
    spans_collection.create_index([("service_name", 1), ("start_time", -1)])
    spans_collection.create_index([("name", 1), ("start_time", -1)])
    spans_collection.create_index([("span_id", 1)])
    
    logger.info("Database initialized successfully")
    
    yield
    
    # Cleanup
    if mongo_client:
        mongo_client.close()
    logger.info("Database connection closed")


# Initialize FastAPI app
app = FastAPI(
    title="OpenTelemetry Span Collector",
    description="Collects and stores OpenTelemetry spans in MongoDB",
    version="1.0.0",
    lifespan=lifespan
)


def calculate_duration_ms(start_time: datetime, end_time: Optional[datetime]) -> Optional[float]:
    """Calculate duration in milliseconds."""
    if end_time is None:
        return None
    delta = end_time - start_time
    return delta.total_seconds() * 1000


@app.post("/v1/traces", response_model=SpanResponseDTO, status_code=201)
async def create_span(span_data: SpanCreateDTO):
    """
    Receive and store a span from OTLP exporter.
    
    This endpoint accepts OTLP trace data and stores it in MongoDB.
    """
    try:
        # Calculate duration
        duration_ms = calculate_duration_ms(span_data.start_time, span_data.end_time)
        
        # Get MongoDB collection
        db = mongo_client[DATABASE_NAME]
        spans_collection = db["spans"]
        
        # Create span document
        span_dict = {
            "_id": f"{span_data.trace_id}_{span_data.span_id}",
            "trace_id": span_data.trace_id,
            "span_id": span_data.span_id,
            "parent_span_id": span_data.parent_span_id,
            "name": span_data.name,
            "kind": span_data.kind,
            "status_code": span_data.status_code,
            "status_message": span_data.status_message,
            "start_time": span_data.start_time,
            "end_time": span_data.end_time,
            "duration_ms": duration_ms,
            "service_name": span_data.service_name,
            "attributes": span_data.attributes,
            "resource_attributes": span_data.resource_attributes,
            "events": [e.model_dump() for e in span_data.events] if span_data.events else None,
            "links": [l.model_dump() for l in span_data.links] if span_data.links else None,
            "received_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        spans_collection.insert_one(span_dict)
        
        logger.info(f"Stored span: {span_data.name} (trace={span_data.trace_id[:8]}...)")
        
        return SpanResponseDTO(
            id=span_dict["_id"],
            trace_id=span_dict["trace_id"],
            span_id=span_dict["span_id"],
            parent_span_id=span_dict["parent_span_id"],
            name=span_dict["name"],
            kind=span_dict["kind"],
            status_code=span_dict["status_code"],
            status_message=span_dict["status_message"],
            start_time=span_dict["start_time"],
            end_time=span_dict["end_time"],
            duration_ms=span_dict["duration_ms"],
            service_name=span_dict["service_name"],
            attributes=span_dict["attributes"],
            resource_attributes=span_dict["resource_attributes"],
            events=[SpanEventDTO(**e) for e in span_dict["events"]] if span_dict["events"] else None,
            links=[SpanLinkDTO(**l) for l in span_dict["links"]] if span_dict["links"] else None,
            received_at=span_dict["received_at"]
        )
        
    except Exception as e:
        logger.error(f"Error storing span: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to store span: {str(e)}")


@app.get("/v1/traces/{trace_id}", response_model=TraceResponseDTO)
async def get_trace(trace_id: str):
    """Retrieve all spans for a given trace ID."""
    try:
        db = mongo_client[DATABASE_NAME]
        spans_collection = db["spans"]
        
        # Find all spans for this trace
        span_docs = list(spans_collection.find({"trace_id": trace_id}).sort("start_time", 1))
        
        if not span_docs:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        # Convert to response DTOs
        spans = []
        for doc in span_docs:
            spans.append(SpanResponseDTO(
                id=doc["_id"],
                trace_id=doc["trace_id"],
                span_id=doc["span_id"],
                parent_span_id=doc.get("parent_span_id"),
                name=doc["name"],
                kind=doc.get("kind"),
                status_code=doc.get("status_code"),
                status_message=doc.get("status_message"),
                start_time=doc["start_time"],
                end_time=doc.get("end_time"),
                duration_ms=doc.get("duration_ms"),
                service_name=doc["service_name"],
                attributes=doc.get("attributes"),
                resource_attributes=doc.get("resource_attributes"),
                events=[SpanEventDTO(**e) for e in doc.get("events", [])] if doc.get("events") else None,
                links=[SpanLinkDTO(**l) for l in doc.get("links", [])] if doc.get("links") else None,
                received_at=doc["received_at"]
            ))
        
        # Find root span (no parent)
        root_span = next((s for s in spans if s.parent_span_id is None), None)
        
        # Calculate trace-level metrics
        start_time = min(s.start_time for s in spans)
        end_times = [s.end_time for s in spans if s.end_time]
        end_time = max(end_times) if end_times else None
        duration_ms = calculate_duration_ms(start_time, end_time)
        services = list(set(s.service_name for s in spans))
        
        return TraceResponseDTO(
            trace_id=trace_id,
            span_count=len(spans),
            root_span=root_span,
            spans=spans,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            services=services
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trace: {str(e)}")


@app.get("/v1/spans", response_model=list[SpanResponseDTO])
async def list_spans(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    span_name: Optional[str] = Query(None, description="Filter by span name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of spans to return")
):
    """List recent spans with optional filtering."""
    try:
        db = mongo_client[DATABASE_NAME]
        spans_collection = db["spans"]
        
        # Build query
        query = {}
        if service_name:
            query["service_name"] = service_name
        if span_name:
            query["name"] = span_name
        
        # Execute query
        span_docs = list(
            spans_collection.find(query)
            .sort("start_time", -1)
            .limit(limit)
        )
        
        # Convert to response DTOs
        spans = []
        for doc in span_docs:
            spans.append(SpanResponseDTO(
                id=doc["_id"],
                trace_id=doc["trace_id"],
                span_id=doc["span_id"],
                parent_span_id=doc.get("parent_span_id"),
                name=doc["name"],
                kind=doc.get("kind"),
                status_code=doc.get("status_code"),
                status_message=doc.get("status_message"),
                start_time=doc["start_time"],
                end_time=doc.get("end_time"),
                duration_ms=doc.get("duration_ms"),
                service_name=doc["service_name"],
                attributes=doc.get("attributes"),
                resource_attributes=doc.get("resource_attributes"),
                events=[SpanEventDTO(**e) for e in doc.get("events", [])] if doc.get("events") else None,
                links=[SpanLinkDTO(**l) for l in doc.get("links", [])] if doc.get("links") else None,
                received_at=doc["received_at"]
            ))
        
        return spans
        
    except Exception as e:
        logger.error(f"Error listing spans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list spans: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "span-collector"}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)