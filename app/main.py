
from fastapi import FastAPI

from app.routers.products import router as products_router
from app.routers.auth import router as auth_router


app = FastAPI(
    title="FDS DevOps Automation API",
    version="3.0.0",
    description=(
        "FDS DevOps Automation API with "
        "Products Management and Authentication"
    )
)


app.include_router(products_router)
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "FDS DevOps Application is running",
        "version": "2.0.0"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }
