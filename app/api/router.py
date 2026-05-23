from fastapi import APIRouter

from app.api import admin, public

api_router = APIRouter()
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
