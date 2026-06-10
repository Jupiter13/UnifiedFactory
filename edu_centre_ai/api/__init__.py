"""FastAPI application for EDU_CENTRE AI."""

from edu_centre_ai.api.app import create_app, app
from edu_centre_ai.api.routes import router


__all__ = ["create_app", "app", "router"]