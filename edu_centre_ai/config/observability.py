"""Observability setup for EDU_CENTRE AI.

Provides Prometheus metrics and OpenTelemetry tracing configuration.
"""

import logging
from typing import Optional

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

logger = logging.getLogger(__name__)


# Global registry
REGISTRY = CollectorRegistry()


# Custom Metrics
AI_LATENCY = Histogram(
    "ai_latency_seconds",
    "AI response latency in seconds",
    ["endpoint", "intent"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
    registry=REGISTRY,
)

TOOL_CALLS = Counter(
    "tool_calls_total",
    "Total number of tool calls",
    ["tool_name", "success"],
    registry=REGISTRY,
)

INTENT_CLASSIFICATION = Counter(
    "intent_classification_total",
    "Total intent classifications",
    ["intent"],
    registry=REGISTRY,
)

RECOMMENDATION_REQUESTS = Counter(
    "recommendation_requests_total",
    "Total recommendation requests",
    registry=REGISTRY,
)

QUIZ_GRADING_REQUESTS = Counter(
    "quiz_grading_requests_total",
    "Total quiz grading requests",
    registry=REGISTRY,
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of active AI sessions",
    registry=REGISTRY,
)

NODE_EXECUTIONS = Counter(
    "node_executions_total",
    "Total node executions",
    ["node_name", "status"],
    registry=REGISTRY,
)


def record_latency(endpoint: str, intent: str, duration: float) -> None:
    """Record AI response latency.

    Args:
        endpoint: API endpoint name
        intent: Detected intent
        duration: Duration in seconds
    """
    AI_LATENCY.labels(endpoint=endpoint, intent=intent).observe(duration)


def record_tool_call(tool_name: str, success: bool) -> None:
    """Record tool call.

    Args:
        tool_name: Name of the tool called
        success: Whether the call succeeded
    """
    TOOL_CALLS.labels(
        tool_name=tool_name,
        success="true" if success else "false",
    ).inc()


def record_intent(intent: str) -> None:
    """Record intent classification.

    Args:
        intent: Classified intent
    """
    INTENT_CLASSIFICATION.labels(intent=intent).inc()


def record_recommendation_request() -> None:
    """Record a recommendation request."""
    RECOMMENDATION_REQUESTS.inc()


def record_quiz_grading_request() -> None:
    """Record a quiz grading request."""
    QUIZ_GRADING_REQUESTS.inc()


def increment_active_sessions() -> None:
    """Increment active sessions gauge."""
    ACTIVE_SESSIONS.inc()


def decrement_active_sessions() -> None:
    """Decrement active sessions gauge."""
    ACTIVE_SESSIONS.dec()


def record_node_execution(node_name: str, status: str) -> None:
    """Record node execution.

    Args:
        node_name: Name of the node
        status: Execution status (success, error)
    """
    NODE_EXECUTIONS.labels(node_name=node_name, status=status).inc()


class MetricsMiddleware:
    """FastAPI middleware for recording request metrics."""

    def __init__(self, app):
        """Initialize middleware.

        Args:
            app: FastAPI application
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process request and record metrics.

        Args:
            scope: Request scope
            receive: Receive function
            send: Send function
        """
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path.startswith("/ai"):
                increment_active_sessions()
                try:
                    await self.app(scope, receive, send)
                finally:
                    decrement_active_sessions()
            else:
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


# OpenTelemetry Configuration
def setup_tracing(
    service_name: str = "edu-centre-ai",
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """Setup OpenTelemetry tracing.

    Args:
        service_name: Name of the service
        endpoint: OTLP endpoint (e.g., Jaeger collector)
        api_key: Optional API key for tracing service
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })

        # Create provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter if endpoint provided
        if endpoint:
            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                insecure=True,
            )
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)

        # Set as global provider
        trace.set_tracer_provider(provider)

        logger.info(f"OpenTelemetry tracing configured for {service_name}")

    except ImportError:
        logger.warning("OpenTelemetry not available, tracing disabled")
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")


def setup_langsmith(
    api_key: str,
    project: str = "edu-centre-ai",
    endpoint: str = "https://api.smith.langchain.com",
) -> None:
    """Setup LangSmith tracing.

    Args:
        api_key: LangSmith API key
        project: Project name
        endpoint: LangSmith endpoint
    """
    try:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint

        logger.info(f"LangSmith tracing configured for project: {project}")

    except Exception as e:
        logger.error(f"Failed to setup LangSmith: {e}")