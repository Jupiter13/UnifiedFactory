"""Configuration module for EDU_CENTRE AI."""

from edu_centre_ai.config.settings import Settings, get_settings
from edu_centre_ai.config.prompts import (
    EDU_TUTOR_PROMPT,
    EDU_RECOMMENDER_PROMPT,
    SYSTEM_PROMPTS,
)


__all__ = [
    "Settings",
    "get_settings",
    "EDU_TUTOR_PROMPT",
    "EDU_RECOMMENDER_PROMPT",
    "SYSTEM_PROMPTS",
]