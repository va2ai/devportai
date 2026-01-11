"""OpenTelemetry tracing setup for RAG system"""
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from typing import Optional
from contextlib import contextmanager


# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

# Create tracer provider
tracer_provider = TracerProvider(
    resource=Resource.create({"service.name": "rag-fact-check-api"})
)
tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

# Set the tracer provider
trace.set_tracer_provider(tracer_provider)

# Get the global tracer
tracer = trace.get_tracer(__name__)


def instrument_app(app):
    """Instrument FastAPI app with OpenTelemetry"""
    FastAPIInstrumentor.instrument_app(app)


class TracingSpans:
    """Enum-like class for span names"""
    RETRIEVAL = "retrieval"
    DRAFT_GENERATION = "draft_generation"
    VERIFICATION = "verification_check"
    CHAT_REQUEST = "chat_request"


@contextmanager
def create_span(span_name: str, attributes: Optional[dict] = None):
    """
    Context manager for creating spans

    Args:
        span_name: Name of the span
        attributes: Optional attributes to add to the span

    Yields:
        The span object
    """
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(key, value)
                else:
                    span.set_attribute(key, str(value))
        yield span


def set_span_attribute(span, key: str, value):
    """Safely set span attribute"""
    if span:
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(key, value)
        else:
            try:
                span.set_attribute(key, str(value))
            except Exception:
                pass


def set_span_status(span, status: str, description: str = ""):
    """Set span status"""
    if span:
        from opentelemetry.trace import Status, StatusCode

        if status == "success":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description))


def record_span_event(span, event_name: str, attributes: Optional[dict] = None):
    """Record an event on the span"""
    if span:
        span.add_event(event_name, attributes or {})
