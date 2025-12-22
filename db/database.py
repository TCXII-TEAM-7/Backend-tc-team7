# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# "postgresql://postgres:pg_for_test@localhost:5432/doxa_callcenter"
SQLALCHEMY_DATABASE_URL = (
    "postgresql://tcxii_user:w9OQanO9T1N8Sa5sEPpKS93rElXMb98y@dpg-d54splshg0os739o11p0-a.virginia-postgres.render.com/tcxii"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
