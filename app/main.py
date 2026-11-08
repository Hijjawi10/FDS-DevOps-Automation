
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, Base
from app import models
from app.routers.products import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("TESTING") != "1":
        Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="FDS DevOps Automation API",
    version="3.0.0",
    lifespan=lifespan
)


app.include_router(products_router)


@app.get("/")
def home():
    return {
        "message": "FDS DevOps Application is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }
