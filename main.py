
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FDS DevOps Application is running"}

@app.get("/health")
def health():
    return {"status": "ok"}