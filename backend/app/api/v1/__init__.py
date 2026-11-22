from fastapi import APIRouter
from app.api.v1.places import router as places_router

api_router = APIRouter()
api_router.include_router(places_router)
