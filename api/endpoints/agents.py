# api/endpoints/agents.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session

from db.database import get_db
import db.models as models
from auth.security import get_password_hash, get_current_admin


router = APIRouter(prefix="/agents", tags=["agents"])


# --------- SCHEMAS ---------

class AgentBase(BaseModel):
    number: str
    email: EmailStr


class AgentCreate(AgentBase):
    password: str


class AgentUpdate(BaseModel):
    number: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class AgentRead(AgentBase):
    id: int

    class Config:
        from_attributes = True   # ou orm_mode = True si Pydantic v1


class AdminCreate(BaseModel):
    number: str
    email: EmailStr
    password: str


# --------- ROUTES ---------

# CREATE
@router.post(
    "/",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    # vérifier si l'email existe déjà
    existing_agent = (
        db.query(models.Agent)
        .filter(models.Agent.email == agent_in.email)
        .first()
    )
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà utilisé",
        )

    # créer l'agent avec mot de passe hashé
    #hashed_password = get_password_hash(agent_in.password)

    agent = models.Agent(
        number=agent_in.number,
        email=agent_in.email,
        password=agent_in.password,  #hashed_password
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


# LIST
@router.get("/", response_model=List[AgentRead])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(models.Agent).all()
    return agents


# GET by id
@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent non trouvé",
        )
    return agent


# UPDATE (PUT partiel)
@router.put("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: int,
    agent_in: AgentUpdate,
    db: Session = Depends(get_db),
):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent non trouvé",
        )

    # si email envoyé, vérifier qu'il n'est pas utilisé par un autre agent
    if agent_in.email:
        existing_agent = (
            db.query(models.Agent)
            .filter(
                models.Agent.email == agent_in.email,
                models.Agent.id != agent_id,
            )
            .first()
        )
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email déjà utilisé par un autre agent",
            )

    # appliquer seulement les champs présents
    if agent_in.number is not None:
        agent.number = agent_in.number
    if agent_in.email is not None:
        agent.email = agent_in.email
    if agent_in.password is not None:
        agent.password = get_password_hash(agent_in.password)

    db.commit()
    db.refresh(agent)
    return agent


# DELETE
@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent non trouvé",
        )

    db.delete(agent)
    db.commit()
    # 204: pas de contenu à renvoyer
