from dataclasses import dataclass, field
from typing import Protocol

from app.models import QuestionType


@dataclass
class GradingContext:
    question_type: QuestionType
    question: str
    response: str
    max_marks: float
    correct_option: str | None = None
    model_answer: str | None = None
    rubric_points: list[dict] = field(default_factory=list)


@dataclass
class GradeProposal:
    score: float
    feedback: str
    evidence: list[str] = field(default_factory=list)
    needs_review: bool = False


class Grader(Protocol):
    def grade(self, context: GradingContext) -> GradeProposal: ...

