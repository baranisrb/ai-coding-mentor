"""Pydantic models describing incoming API requests."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"


class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Source code submitted by the user")
    language: Language = Field(..., description="Programming language of the submitted code")
    difficulty: Difficulty = Field(
        default=Difficulty.BEGINNER,
        description="Skill level the mentor should tailor explanations to",
    )
    question: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional free-form question the user has about the code",
    )

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("code must not be empty or whitespace-only")
        return value


class HintRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: Language
    difficulty: Difficulty = Difficulty.BEGINNER

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("code must not be empty or whitespace-only")
        return value
