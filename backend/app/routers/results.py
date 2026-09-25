from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.dependencies import SessionDep, get_current_user
from app.models import Answer, Exam, ExamStatus, Grade, Question, Submission, User

router = APIRouter(tags=["results"])


@router.get("/me/results")
def my_results(session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    submissions = session.exec(select(Submission).where(Submission.user_id == user.id)).all()
    results = []
    for submission in submissions:
        exam = session.get(Exam, submission.exam_id)
        if exam is None or exam.status != ExamStatus.published:
            continue
        items = []
        answers = session.exec(select(Answer).where(Answer.submission_id == submission.id)).all()
        for answer in answers:
            question = session.get(Question, answer.question_id)
            grade = session.exec(select(Grade).where(Grade.answer_id == answer.id)).first()
            items.append({"question_id": question.id, "question": question.text,
                          "response": answer.response, "max_marks": question.max_marks,
                          "grade": grade})
        results.append({"submission_id": submission.id, "exam_id": exam.id,
                        "exam_title": exam.title, "submitted_at": submission.submitted_at,
                        "answers": items})
    return results

