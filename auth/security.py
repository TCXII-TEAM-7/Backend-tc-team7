import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional

from db.database import get_db
import  db.models   as models

SECRET_KEY = "change_me_en_valeur_secrete_longue"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100

# on garde le contexte pour plus tard (quand tu voudras remettre le hash)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ✅ ADD THIS - Token blacklist for logout functionality
token_blacklist = set()


# ---------- MOTS DE PASSE (VERSION SIMPLE SANS HASH) ----------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Version TEMPORAIRE : compare en clair.
    plain_password : ce que l'agent envoie au login.
    hashed_password : valeur stockée en DB (actuellement aussi en clair).
    """
    return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    """
    Version TEMPORAIRE : ne pas hasher, renvoyer le mot de passe tel quel.
    Quand tu seras prêt à utiliser le hash, tu remplaceras par :
        return pwd_context.hash(password)
    """
    return password


# ---------- JWT ---------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    # Ensure 'sub' is a string (PyJWT requirement)
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_agent(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.Agent:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ✅ ADD THIS - Check if token is blacklisted
    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token révoqué. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id: Optional[int] = None
        sub = payload.get("sub")
        # Handle both string and int formats
        if isinstance(sub, str):
            agent_id = int(sub)
        else:
            agent_id = sub
        if agent_id is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if agent is None:
        raise credentials_exception
    return agent


def verify_token(token: str, db: Session) -> models.Agent:
    """
    Reusable function for programmatic token verification (used by middleware).
    Raises HTTPException(401) if token is invalid or agent not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # ✅ ADD THIS - Check if token is blacklisted
    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token révoqué. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if isinstance(sub, str):
            agent_id = int(sub)
        else:
            agent_id = sub
        if agent_id is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if agent is None:
        raise credentials_exception
    return agent


def get_current_admin(
    current_agent: models.Agent = Depends(get_current_agent),
) -> models.Agent:
    """Vérifie que l'agent actuel est un admin"""
    if current_agent.role != models.Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_agent