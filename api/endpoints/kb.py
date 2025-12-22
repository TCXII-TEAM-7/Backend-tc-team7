from fastapi import APIRouter
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from db.database import get_db
import db.models as models
from auth.security import get_current_agent

# Require a valid JWT for every /kb route; handlers can accept
# `current_agent: models.Agent = Depends(get_current_agent)` to access it.
router = APIRouter(prefix="/kb", tags=["kb"], dependencies=[Depends(get_current_agent)])


class kbentry_payload(BaseModel):
    question: str
    answer: str
    # optional category string (matches DB `category` column)
    category: Optional[str] = None


@router.post("/", status_code=201)
def create_kb_entry(
    payload: kbentry_payload,
    db: Session = Depends(get_db),
    current_agent: models.Agent = Depends(get_current_agent),
):
    kb_entry = models.kbase_entry(
        question=payload.question,
        answer=payload.answer,
        category=payload.category,
    )
    db.add(kb_entry)
    db.commit()
    db.refresh(kb_entry)
    return {
        "id": kb_entry.id,
        "question": kb_entry.question,
        "answer": kb_entry.answer,
        "category": kb_entry.category,
        "message": "Knowledge base entry created successfully.",
    }
    
@router.get("/", status_code=200)
def list_kb(db: Session = Depends(get_db), current_agent: models.Agent = Depends(get_current_agent)): 
    kb_entries = db.query(models.kbase_entry).all()
    return kb_entries    

@router.delete("/{kb_id}", status_code=200)
def delete_kb_entry(kb_id:int , db : Session = Depends(get_db)):
    kb_entry = db.query(models.kbase_entry).filter(models.kbase_entry.id == kb_id).first()
    if not kb_entry:
        return {"message": "Knowledge base entry not found."}
    db.delete(kb_entry)
    db.commit()
    return {"message": "Knowledge base entry deleted successfully."}

@router.put("/{kb_id}", status_code=200)
def update_kb_entry(kb_id:int, payload: kbentry_payload, db : Session = Depends(get_db)):
    kb_entry = db.query(models.kbase_entry).filter(models.kbase_entry.id == kb_id).first()
    if not kb_entry:
        return {"message": "Knowledge base entry not found."}
    kb_entry.question = payload.question
    kb_entry.answer = payload.answer
    kb_entry.category = payload.category
    db.commit()
    db.refresh(kb_entry)
    return {
        "id": kb_entry.id,
        "question": kb_entry.question,
        "answer": kb_entry.answer,
        "category": kb_entry.category,
        "message": "Knowledge base entry updated successfully.",
    }