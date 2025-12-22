from fastapi import APIRouter
from api.endpoints import agents, auth, callsession, kb

api_router = APIRouter()
api_router.include_router(agents.router)
api_router.include_router(auth.router)
api_router.include_router(callsession.router)
api_router.include_router(kb.router)