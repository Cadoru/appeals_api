from fastapi import APIRouter

from app.api.admin import appeals, auth, topics, users

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["admin-auth"])
router.include_router(users.router, prefix="/users", tags=["admin-users"])
router.include_router(topics.router, prefix="/topics", tags=["admin-topics"])
router.include_router(appeals.router, prefix="/appeals", tags=["admin-appeals"])
