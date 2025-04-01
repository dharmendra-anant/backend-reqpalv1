from uuid import uuid4

from pydantic import BaseModel, Field


class Score(BaseModel):
    """Score for a resume."""

    score: float = Field(..., alias="score")


class ScoreExplained(BaseModel):
    """Score explained for a resume."""

    score: float = Field(..., alias="score")
    explanation: str = Field(..., alias="explanation")


class ResumeScoreConsolidated(BaseModel):
    """Score results for a resume."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default_factory=lambda: f"Anonymous+{str(uuid4())[:4]}")
    ai_score: Score | ScoreExplained = Field(..., alias="aiScore")
    ats_score: Score | ScoreExplained = Field(..., alias="atsScore")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True