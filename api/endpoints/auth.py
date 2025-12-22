from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db.database import get_db
import db.models as models
from auth.security import (
    verify_password, 
    create_access_token,
    token_blacklist  # ✅ Import the blacklist
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


class LoginAgent(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login_json(payload: LoginAgent, db: Session = Depends(get_db)):
    agent = (
        db.query(models.Agent)
        .filter(models.Agent.email == payload.email)
        .first()
    )
    
    if agent is None or not verify_password(payload.password, agent.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    access_token = create_access_token(data={"sub": agent.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout endpoint - invalidates the current token
    """
    token = credentials.credentials
    
    # Add token to blacklist
    token_blacklist.add(token)
    
    return {
        "message": "Déconnexion réussie",
        "detail": "Le token a été invalidé"
    }
