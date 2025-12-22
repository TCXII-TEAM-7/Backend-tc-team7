# api/endpoints/agent.py
from fastapi import APIRouter, HTTPException, status,  Depends
from pydantic import BaseModel, EmailStr
from typing import List
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/agents", tags=["agents"])

# "Base de données" en mémoire pour tester
agents_db: list[models.Agent] = []
next_id = 1


class AgentCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class AgentRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr


# CREATE
@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):

    # vérifier email unique (dans la DB)
    existing_agent = db.query(models.Agent)\
        .filter(models.Agent.email == agent_in.email)\
        .first()

    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà utilisé",
        )

    agent = models.Agent(
        full_name=agent_in.full_name,
        email=agent_in.email,
        password=agent_in.password,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


# LIST
@router.get("/", response_model=List[AgentRead])
def list_agents():
    return [AgentRead(id=a.id, full_name=a.full_name, email=a.email) for a in agents_db]
