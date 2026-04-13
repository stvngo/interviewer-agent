from fastapi import APIRouter, HTTPException, Query

from app.api.v1.schemas import QuestionListResponse, QuestionOut
from app.services import question_loader

router = APIRouter()


@router.get("/", response_model=QuestionListResponse)
async def list_questions(
    difficulty: str | None = Query(None, description="Filter by Easy, Medium, or Hard"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> QuestionListResponse:
    questions, total = question_loader.get_filtered(difficulty=difficulty, skip=skip, limit=limit)
    return QuestionListResponse(questions=questions, total=total, skip=skip, limit=limit)


@router.get("/random", response_model=QuestionOut)
async def random_question(
    difficulty: str | None = Query(None, description="Filter by Easy, Medium, or Hard"),
) -> QuestionOut:
    q = question_loader.get_random(difficulty=difficulty)
    if q is None:
        raise HTTPException(status_code=404, detail="No questions found for the given filter")
    return q


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(question_id: int) -> QuestionOut:
    q = question_loader.get_by_id(question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    return q
