from pydantic import BaseModel, EmailStr, Field

from app.models.entities import QuestionType


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool


class RubricPointInput(BaseModel):
    description: str
    marks: float = Field(gt=0)
    keywords: list[str] = []


class QuestionInput(BaseModel):
    type: QuestionType
    text: str
    max_marks: float = Field(gt=0)
    options: list[str] | None = None
    correct_option: str | None = None
    model_answer: str | None = None
    rubric_points: list[RubricPointInput] = []


class ExamCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    duration_min: int = Field(gt=0)


class AnswerInput(BaseModel):
    question_id: int
    response: str


class SubmissionInput(BaseModel):
    answers: list[AnswerInput]


class GradeOverride(BaseModel):
    score: float = Field(ge=0)
    feedback: str = ""


class GradeResponse(BaseModel):
    id: int
    answer_id: int
    score: float
    feedback: str
    evidence: list[str]
    graded_by: str
    needs_review: bool


class ResultItem(BaseModel):
    question_id: int
    question: str
    response: str
    max_marks: float
    grade: GradeResponse | None


class SubmissionResult(BaseModel):
    submission_id: int
    exam_id: int
    exam_title: str
    submitted_at: str
    answers: list[ResultItem]


class AdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ActiveUpdate(BaseModel):
    is_active: bool
