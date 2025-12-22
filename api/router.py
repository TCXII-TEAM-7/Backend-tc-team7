# api/router.py
from fastapi import APIRouter
from api.endpoints import agents

api_router = APIRouter()
api_router.include_router(agents.router)
