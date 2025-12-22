# api/endpoints/call_session.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
import   db.models as  models
from db.models import ClientType, FinalStatus
from auth.security import get_current_agent, get_current_admin

router = APIRouter(prefix="/call-sessions", tags=["call_sessions"])


# --------- SCHEMAS Pydantic ---------

class CallSessionBase(BaseModel):
    client_type: ClientType
    reason: str
    ai_query: str


class CallSessionCreate(CallSessionBase):
    # au moment de la création, on peut laisser result / final_status vides
    result: str | None = None
    final_status: FinalStatus | None = None


class CallSessionRead(CallSessionBase):
    id: int
    agent_id: int
    result: str | None = None
    final_status: FinalStatus | None = None

    class Config:
        from_attributes = True  # ou orm_mode=True si Pydantic v1


# --------- ROUTES ---------


# CREATE : l'agent connecté crée une session
@router.post(
    "/",
    response_model=CallSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_call_session(
    session_in: CallSessionCreate,
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent)
):
    call_session = models.CallSession(
        agent_id=current_agent.id,
        client_type=session_in.client_type,
        reason=session_in.reason,
        ai_query=session_in.ai_query,
        result=session_in.result,
        final_status=session_in.final_status,
    )

    db.add(call_session)
    db.commit()
    db.refresh(call_session)
    return call_session


# LIST : tout agent peut voir TOUTES les sessions
@router.get("/", response_model=List[CallSessionRead])
def list_all_call_sessions(
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent),
):
    sessions = (
        db.query(models.CallSession)
        .order_by(models.CallSession.id.desc())
        .all()
    )
    return sessions


# GET by id : retourner n'importe quelle session
@router.get("/{session_id}", response_model=CallSessionRead)
def get_call_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent),
):
    session_obj = db.query(models.CallSession).filter(
        models.CallSession.id == session_id,
    ).first()

    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée",
        )

    return session_obj


# UPDATE : seul un admin peut modifier une session
@router.put("/{session_id}", response_model=CallSessionRead)
def update_call_session(
    session_id: int,
    session_in: CallSessionCreate,
    db: Session = Depends(get_db),
    current_admin: models.Agent = Depends(get_current_admin),
):
    session_obj = db.query(models.CallSession).filter(
        models.CallSession.id == session_id,
    ).first()

    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée",
        )

    # Mettre à jour les champs
    session_obj.client_type = session_in.client_type
    session_obj.reason = session_in.reason
    session_obj.ai_query = session_in.ai_query
    if session_in.result is not None:
        session_obj.result = session_in.result
    if session_in.final_status is not None:
        session_obj.final_status = session_in.final_status

    db.commit()
    db.refresh(session_obj)
    return session_obj


# DELETE : seul un admin peut supprimer une session
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_admin: models.Agent = Depends(get_current_admin),
):
    session_obj = db.query(models.CallSession).filter(
        models.CallSession.id == session_id,
    ).first()

    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée",
        )

    db.delete(session_obj)
    db.commit()
