from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.dependencies import SessionDep, get_current_user
from app.models import Answer, Exam, ExamStatus, Question, Submission, User
from app.schemas import SubmissionInput

router = APIRouter(tags=["submissions"])


@router.post("/exams/{exam_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_exam(exam_id: int, payload: SubmissionInput, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    
    exam = session.get(Exam, exam_id)
    if exam is None or exam.status != ExamStatus.open:
        raise HTTPException(status_code=404, detail="Open exam not found")
    submitted_ids = [answer.question_id for answer in payload.answers]
    if len(submitted_ids) != len(set(submitted_ids)):
        raise HTTPException(status_code=422, detail="Each question can only be answered once")
    valid_ids = set(session.exec(select(Question.id).where(Question.exam_id == exam_id)).all())
    if any(question_id not in valid_ids for question_id in submitted_ids):
        raise HTTPException(status_code=422, detail="Answer contains a question outside this exam")
    submission = Submission(exam_id=exam_id, user_id=user.id)
    session.add(submission)
    session.flush()
    for answer in payload.answers:
        session.add(Answer(submission_id=submission.id, **answer.model_dump()))
    session.commit()
    session.refresh(submission)
    return {"id": submission.id, "exam_id": exam_id, "status": submission.status}

