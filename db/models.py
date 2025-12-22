from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from db.database import Base


class ClientType(str, PyEnum):
    INDIVIDUAL = "individual"   # client particulier
    COMPANY = "company"         # client entreprise


class FinalStatus(str, PyEnum):
    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"




class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    call_sessions = relationship("CallSession", back_populates="agent")


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)


    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

   
    client_type = Column(
        Enum(ClientType, name="client_type_enum"),
        nullable=False,
    )


   
    reason = Column(String, nullable=False)

  
    ai_query = Column(Text, nullable=False)

    result = Column(String, nullable=True)

   
    final_status = Column(
        Enum(FinalStatus, name="final_status_enum"),
        nullable=False,
    )

    
    agent = relationship("Agent", back_populates="call_sessions")

class kbase_entry(Base):
    __tablename__ = "kbase_entries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)    
    category = Column(String, nullable=True) 

