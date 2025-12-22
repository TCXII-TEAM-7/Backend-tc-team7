# main.py
from fastapi import FastAPI
from api.endpoints import kb
from api.router import api_router
from database import engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(api_router)
