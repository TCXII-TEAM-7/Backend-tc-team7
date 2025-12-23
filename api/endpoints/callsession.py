# api/endpoints/call_session.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
import db.models as models
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


#  SEARCH with FILTERS
@router.get("/search", response_model=List[CallSessionRead])
def search_call_sessions(
    # Filter parameters that we will searchh based on
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    client_type: Optional[ClientType] = Query(None, description="Filter by client type: individual or company"),
    reason: Optional[str] = Query(None, description="Search in reason (partial match)"),
    final_status: Optional[FinalStatus] = Query(None, description="Filter by final status: satisfied or not_satisfied"),
    ai_query_keyword: Optional[str] = Query(None, description="Search in AI query (partial match)"),
    result_keyword: Optional[str] = Query(None, description="Search in result (partial match)"),
    
    # Pagination partt 
    skip: int = Query(0, ge=0, description="Number of records to skip"), #for the pagination 
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent),
):

    
    # Start building the query
    query = db.query(models.CallSession)
    
    # Apply filters only if provided
    if agent_id is not None:
        query = query.filter(models.CallSession.agent_id == agent_id)
    
    if client_type is not None:
        query = query.filter(models.CallSession.client_type == client_type)
    
    if reason is not None:
        # Partial match search (case-insensitive)
        query = query.filter(models.CallSession.reason.ilike(f"%{reason}%"))
    
    if final_status is not None:
        query = query.filter(models.CallSession.final_status == final_status)
    
    if ai_query_keyword is not None:
        query = query.filter(models.CallSession.ai_query.ilike(f"%{ai_query_keyword}%"))
    
    if result_keyword is not None:
        query = query.filter(models.CallSession.result.ilike(f"%{result_keyword}%"))
    
    query = query.order_by(models.CallSession.id.desc())
    
    sessions = query.offset(skip).limit(limit).all()
    
    return sessions


# Get only MY sessions (current agent)
@router.get("/my-sessions", response_model=List[CallSessionRead])
def get_my_call_sessions(
    client_type: Optional[ClientType] = Query(None, description="Filter by client type"),
    final_status: Optional[FinalStatus] = Query(None, description="Filter by final status"),
    reason: Optional[str] = Query(None, description="Search in reason"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent),
):
   
    query = db.query(models.CallSession).filter(
        models.CallSession.agent_id == current_agent.id
    )
    
    if client_type:
        query = query.filter(models.CallSession.client_type == client_type)
    
    if final_status:
        query = query.filter(models.CallSession.final_status == final_status)
    
    if reason:
        query = query.filter(models.CallSession.reason.ilike(f"%{reason}%"))
    
    query = query.order_by(models.CallSession.id.desc())
    sessions = query.offset(skip).limit(limit).all()
    
    return sessions


# LIST : tout agent peut voir TOUTES les sessions
@router.get("/all", response_model=List[CallSessionRead])
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
@router.get("/session/{session_id}", response_model=CallSessionRead)
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


@router.put("/update/{session_id}", response_model=CallSessionRead)
def update_call_session(
    session_id: int,
    session_in: CallSessionCreate,
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


@router.delete("/delete/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_admin),  # ✅ Only admin can delete
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


# Get statistics
@router.get("/stats")
def get_call_session_stats(
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent),
):
   
    from sqlalchemy import func
    
    # Total sessions
    total = db.query(func.count(models.CallSession.id)).scalar()
    
    # By client type
    by_client_type = db.query(
        models.CallSession.client_type,
        func.count(models.CallSession.id)
    ).group_by(models.CallSession.client_type).all()
    
    # By final status
    by_status = db.query(
        models.CallSession.final_status,
        func.count(models.CallSession.id)
    ).group_by(models.CallSession.final_status).all()
    
    # By agent
    by_agent = db.query(
        models.CallSession.agent_id,
        func.count(models.CallSession.id)
    ).group_by(models.CallSession.agent_id).all()
    
    return {
        "total_sessions": total,
        "by_client_type": {str(ct): count for ct, count in by_client_type},
        "by_final_status": {str(status): count for status, count in by_status},
        "by_agent": {agent_id: count for agent_id, count in by_agent}
    }
