from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.dependencies import SessionDep, get_current_user, require_roles
from app.models import Answer, Exam, ExamStatus, Grade, Question, Role, RubricPoint, Submission, User
from app.schemas import ExamCreate, QuestionInput

router = APIRouter(prefix="/exams", tags=["exams"])
AdminDep = Annotated[User, Depends(require_roles(Role.admin, Role.superadmin))]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_exam(payload: ExamCreate, session: SessionDep, admin: AdminDep):
    exam = Exam(**payload.model_dump(), created_by=admin.id)
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


@router.get("")
def list_exams(session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    statement = select(Exam)
    if user.role == Role.user:
        statement = statement.where(Exam.status == ExamStatus.open)
    return session.exec(statement.order_by(Exam.id.desc())).all()


@router.get("/{exam_id}")
def get_exam(exam_id: int, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    exam = session.get(Exam, exam_id)
    if exam is None or (user.role == Role.user and exam.status != ExamStatus.open):
        raise HTTPException(status_code=404, detail="Exam not found")
    questions = session.exec(select(Question).where(Question.exam_id == exam_id)).all()
    return {"id": exam.id, "title": exam.title, "description": exam.description,
            "duration_min": exam.duration_min, "status": exam.status,
            "questions": [{"id": q.id, "type": q.type, "text": q.text,
                           "max_marks": q.max_marks, "options": q.options}
                          for q in questions]}


@router.post("/{exam_id}/questions", status_code=status.HTTP_201_CREATED)
def create_question(exam_id: int, payload: QuestionInput, session: SessionDep, admin: AdminDep):
    exam = session.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    question_data = payload.model_dump(exclude={"rubric_points"})
    question = Question(exam_id=exam_id, **question_data)
    session.add(question)
    session.flush()
    for point in payload.rubric_points:
        session.add(RubricPoint(question_id=question.id, **point.model_dump()))
    session.commit()
    session.refresh(question)
    return question


@router.post("/{exam_id}/open")
def open_exam(exam_id: int, session: SessionDep, admin: AdminDep):
    exam = session.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.status = ExamStatus.open
    session.add(exam)
    session.commit()
    return {"id": exam.id, "status": exam.status}


@router.post("/{exam_id}/publish")
def publish_exam(exam_id: int, session: SessionDep, admin: AdminDep):
    exam = session.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    submissions = session.exec(select(Submission).where(Submission.exam_id == exam_id)).all()
    for submission in submissions:
        answers = session.exec(select(Answer).where(Answer.submission_id == submission.id)).all()
        if any(session.exec(select(Grade).where(Grade.answer_id == answer.id)).first() is None
               for answer in answers):
            raise HTTPException(status_code=409, detail="All submitted answers must be graded before publishing")
    exam.status = ExamStatus.published
    session.add(exam)
    session.commit()
    return {"id": exam.id, "status": exam.status}
