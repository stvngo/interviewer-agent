from fastapi import APIRouter

from app.api.v1 import auth, users, profiles, resumes, question_banks, questions, rubrics, templates
from app.api.v1 import sessions, rounds, transcripts, code_events, scoring, reports, media
from app.api.v1 import analytics, integrity, admin, health, ws


api_router = APIRouter()

# v1 API
api_router.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/v1/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/v1/profiles", tags=["profiles"])
api_router.include_router(resumes.router, prefix="/v1/resumes", tags=["resumes"])
api_router.include_router(question_banks.router, prefix="/v1/question-banks", tags=["question-banks"])
api_router.include_router(questions.router, prefix="/v1/questions", tags=["questions"])
api_router.include_router(rubrics.router, prefix="/v1/rubrics", tags=["rubrics"])
api_router.include_router(templates.router, prefix="/v1/templates", tags=["templates"])
api_router.include_router(sessions.router, prefix="/v1/sessions", tags=["sessions"])
api_router.include_router(rounds.router, prefix="/v1/rounds", tags=["rounds"])
api_router.include_router(transcripts.router, prefix="/v1/transcripts", tags=["transcripts"])
api_router.include_router(code_events.router, prefix="/v1/code-events", tags=["code-events"])
api_router.include_router(scoring.router, prefix="/v1/scoring", tags=["scoring"])
api_router.include_router(reports.router, prefix="/v1/reports", tags=["reports"])
api_router.include_router(media.router, prefix="/v1/media", tags=["media"])
api_router.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])
api_router.include_router(integrity.router, prefix="/v1/integrity", tags=["integrity"])
api_router.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
api_router.include_router(health.router, prefix="/v1", tags=["health"])
api_router.include_router(ws.router, prefix="/v1", tags=["websocket"])

