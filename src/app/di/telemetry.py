import os


def init_telemetry(service_name: str | None = None, enable_console_exporter: bool = True) -> None:
    """Initialize OpenTelemetry tracing and common automatic instrumentation.

    - Reads OTEL_ environment variables (OTEL_EXPORTER_OTLP_*). If an OTLP exporter
      is available it will be added. A ConsoleSpanExporter is added by default for
      local debugging and when no OTLP endpoint is configured.
    - Instruments `requests` and `sqlalchemy` if the corresponding instrumentation
      packages are available.

    This function is safe to call even when OpenTelemetry packages are not installed
    (it will print a warning and continue).
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        # OTLP exporter is optional - try to import it
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        except Exception:
            OTLPSpanExporter = None

        # Optional instrumentations
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
        except Exception:
            RequestsInstrumentor = None

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        except Exception:
            SQLAlchemyInstrumentor = None

        try:
            from opentelemetry.instrumentation.logging import LoggingInstrumentor
        except Exception:
            LoggingInstrumentor = None

        svc_name = service_name or os.getenv("OTEL_SERVICE_NAME", "medical-pacs")

        resource = Resource.create({"service.name": svc_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Add OTLP exporter pointing to our span collector service
        if OTLPSpanExporter is not None:
            try:
                # Default to localhost:4317 if not set via environment
                otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                print(f"OTLP exporter configured for {otlp_endpoint}")
            except Exception as e:
                print(f"Warning: OTLP exporter could not be initialized: {e}")

        if enable_console_exporter:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        # Auto-instrument common libraries (best-effort)
        if RequestsInstrumentor is not None:
            try:
                RequestsInstrumentor().instrument()
            except Exception as e:
                print(f"Warning: Requests instrumentation failed: {e}")

        if SQLAlchemyInstrumentor is not None:
            try:
                SQLAlchemyInstrumentor().instrument()
            except Exception as e:
                print(f"Warning: SQLAlchemy instrumentation failed: {e}")

        if LoggingInstrumentor is not None:
            try:
                LoggingInstrumentor().instrument(set_logging_format=True)
            except Exception as e:
                print(f"Warning: Logging instrumentation failed: {e}")

        print(f"OpenTelemetry initialized (service={svc_name})")

    except Exception as e:  # pragma: no cover - best-effort initialization
        print(f"Warning: could not initialize OpenTelemetry: {e}")


# Helper context manager to start spans in application code. Returns a no-op context
# manager when opentelemetry is not available so instrumentation calls become
# best-effort and won't raise when packages are missing.
from contextlib import contextmanager


def start_span(name: str, attributes: dict | None = None):
    """Return a context manager that starts an OpenTelemetry span named `name`.

    Usage:
        from app.di.telemetry import start_span

        with start_span("pacs.get_study", {"study.id": study_id}):
            ...

    This function will return a no-op context manager if OpenTelemetry is not
    installed or if tracer creation fails.
    """
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        return tracer.start_as_current_span(name, attributes=attributes or {})
    except Exception:
        @contextmanager
        def _noop():
            yield

        return _noop()