"""SQLAlchemy models and Pydantic DTOs for storing OpenTelemetry spans."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Span(Base):
    """SQLAlchemy model for storing OpenTelemetry spans in MongoDB."""
    
    __tablename__ = "spans"
    
    # MongoDB will use _id as the primary key
    id = Column(String, primary_key=True, doc="MongoDB ObjectId as string")
    
    # Core span identifiers
    trace_id = Column(String, nullable=False, index=True, doc="Trace ID (hex string)")
    span_id = Column(String, nullable=False, index=True, doc="Span ID (hex string)")
    parent_span_id = Column(String, nullable=True, index=True, doc="Parent span ID")
    
    # Span metadata
    name = Column(String, nullable=False, index=True, doc="Span name/operation")
    kind = Column(String, nullable=True, doc="Span kind (INTERNAL, CLIENT, SERVER, etc)")
    status_code = Column(String, nullable=True, doc="Status code (OK, ERROR, UNSET)")
    status_message = Column(String, nullable=True, doc="Status message if error")
    
    # Timing information
    start_time = Column(DateTime, nullable=False, index=True, doc="Span start time (UTC)")
    end_time = Column(DateTime, nullable=True, doc="Span end time (UTC)")
    duration_ms = Column(Float, nullable=True, doc="Duration in milliseconds")
    
    # Service information
    service_name = Column(String, nullable=False, index=True, doc="Service that created span")
    
    # Attributes and metadata
    attributes = Column(JSON, nullable=True, doc="Span attributes/tags as JSON")
    resource_attributes = Column(JSON, nullable=True, doc="Resource attributes")
    events = Column(JSON, nullable=True, doc="Span events as JSON array")
    links = Column(JSON, nullable=True, doc="Span links as JSON array")
    
    # Ingestion metadata
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                        doc="Time span was received by collector")
    
    # Create compound indexes for common queries
    __table_args__ = (
        Index('ix_trace_start', 'trace_id', 'start_time'),
        Index('ix_service_start', 'service_name', 'start_time'),
        Index('ix_name_start', 'name', 'start_time'),
    )


# Pydantic DTOs for API validation and serialization

class SpanEventDTO(BaseModel):
    """Represents an event that occurred during a span."""
    name: str
    timestamp: datetime
    attributes: Optional[dict[str, Any]] = None


class SpanLinkDTO(BaseModel):
    """Represents a link to another span."""
    trace_id: str
    span_id: str
    attributes: Optional[dict[str, Any]] = None


class SpanCreateDTO(BaseModel):
    """DTO for creating a new span (incoming from OTLP)."""
    trace_id: str = Field(..., description="Trace ID (hex string)")
    span_id: str = Field(..., description="Span ID (hex string)")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    
    name: str = Field(..., description="Span operation name")
    kind: Optional[str] = Field(None, description="Span kind")
    status_code: Optional[str] = Field(None, description="Status code")
    status_message: Optional[str] = Field(None, description="Status message")
    
    start_time: datetime = Field(..., description="Span start time")
    end_time: Optional[datetime] = Field(None, description="Span end time")
    
    service_name: str = Field(..., description="Service name")
    attributes: Optional[dict[str, Any]] = Field(None, description="Span attributes")
    resource_attributes: Optional[dict[str, Any]] = Field(None, description="Resource attributes")
    events: Optional[list[SpanEventDTO]] = Field(None, description="Span events")
    links: Optional[list[SpanLinkDTO]] = Field(None, description="Span links")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "1234567890abcdef1234567890abcdef",
                "span_id": "abcdef1234567890",
                "parent_span_id": "1234567890abcdef",
                "name": "pacs.get_study",
                "kind": "INTERNAL",
                "status_code": "OK",
                "start_time": "2024-01-22T10:30:00Z",
                "end_time": "2024-01-22T10:30:01.500Z",
                "service_name": "medical-pacs",
                "attributes": {"study.id": "12345", "http.method": "GET"}
            }
        }


class SpanResponseDTO(BaseModel):
    """DTO for span responses (outgoing from API)."""
    id: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    
    name: str
    kind: Optional[str]
    status_code: Optional[str]
    status_message: Optional[str]
    
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    
    service_name: str
    attributes: Optional[dict[str, Any]]
    resource_attributes: Optional[dict[str, Any]]
    events: Optional[list[SpanEventDTO]]
    links: Optional[list[SpanLinkDTO]]
    
    received_at: datetime
    
    class Config:
        from_attributes = True


class TraceResponseDTO(BaseModel):
    """DTO for trace responses (collection of spans)."""
    trace_id: str
    span_count: int
    root_span: Optional[SpanResponseDTO]
    spans: list[SpanResponseDTO]
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    services: list[str]