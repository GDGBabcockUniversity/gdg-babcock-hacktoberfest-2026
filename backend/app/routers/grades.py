from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.dependencies import SessionDep, require_roles
from app.graders import GradeProposal, GradingContext, get_grader
from app.models import Answer, Exam, Grade, Question, Role, RubricPoint, Submission, User
from app.schemas import GradeOverride

router = APIRouter(tags=["grading"])
AdminDep = Annotated[User, Depends(require_roles(Role.admin, Role.superadmin))]


@router.post("/submissions/{submission_id}/grade")
def grade_submission(submission_id: int, session: SessionDep, admin: AdminDep):
    submission = session.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    grader = get_grader()
    results = []
    answers = session.exec(select(Answer).where(Answer.submission_id == submission_id)).all()
    for answer in answers:
        question = session.get(Question, answer.question_id)
        points = session.exec(select(RubricPoint).where(RubricPoint.question_id == question.id)).all()
        proposal: GradeProposal = grader.grade(GradingContext(
            question_type=question.type,
            question=question.text,
            response=answer.response,
            max_marks=question.max_marks,
            correct_option=question.correct_option,
            model_answer=question.model_answer,
            rubric_points=[{"description": point.description, "marks": point.marks,
                            "keywords": point.keywords} for point in points],
        ))
        record = session.exec(select(Grade).where(Grade.answer_id == answer.id)).first()
        if record is None:
            record = Grade(answer_id=answer.id, score=proposal.score)
        record.score = min(max(proposal.score, 0), question.max_marks)
        record.feedback = proposal.feedback
        record.evidence = proposal.evidence
        record.graded_by = "ai"
        record.needs_review = proposal.needs_review
        session.add(record)
        results.append(record)
    session.commit()
    for grade in results:
        session.refresh(grade)
    submission.status = "graded"
    session.add(submission)
    session.commit()
    return results


@router.patch("/grades/{grade_id}")
def override_grade(grade_id: int, payload: GradeOverride, session: SessionDep, admin: AdminDep):
    grade = session.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")
    answer = session.get(Answer, grade.answer_id)
    question = session.get(Question, answer.question_id)
    if payload.score > question.max_marks:
        raise HTTPException(status_code=422, detail="Score exceeds question maximum")
    grade.score = payload.score
    grade.feedback = payload.feedback
    grade.graded_by = "admin"
    grade.needs_review = False
    session.add(grade)
    session.commit()
    session.refresh(grade)
    return grade

