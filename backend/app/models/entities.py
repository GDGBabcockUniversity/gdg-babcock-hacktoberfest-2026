from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, JSON, String
from sqlmodel import Field, Relationship, SQLModel


class Role(str, Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"


class ExamStatus(str, Enum):
    draft = "draft"
    open = "open"
    closed = "closed"
    published = "published"


class QuestionType(str, Enum):
    objective = "objective"
    short = "short"
    theory = "theory"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    password_hash: str
    role: Role = Field(default=Role.user)
    is_active: bool = True


class Exam(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    duration_min: int = Field(gt=0)
    status: ExamStatus = ExamStatus.draft
    created_by: int = Field(foreign_key="user.id")
    questions: list["Question"] = Relationship(back_populates="exam")


class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exam.id", index=True)
    type: QuestionType
    text: str
    max_marks: float = Field(gt=0)
    options: list[str] | None = Field(default=None, sa_column=Column(JSON))
    correct_option: str | None = None
    model_answer: str | None = None
    exam: Exam | None = Relationship(back_populates="questions")
    rubric_points: list["RubricPoint"] = Relationship(back_populates="question")


class RubricPoint(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    description: str
    marks: float = Field(gt=0)
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    question: Question | None = Relationship(back_populates="rubric_points")


class Submission(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exam.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    status: str = "submitted"
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answers: list["Answer"] = Relationship(back_populates="submission")


class Answer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="submission.id", index=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    response: str
    submission: Submission | None = Relationship(back_populates="answers")
    grade: Optional["Grade"] = Relationship(back_populates="answer")


class Grade(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    answer_id: int = Field(foreign_key="answer.id", unique=True, index=True)
    score: float = Field(ge=0)
    feedback: str = ""
    evidence: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    graded_by: str = "ai"
    needs_review: bool = False
    answer: Answer | None = Relationship(back_populates="grade")
