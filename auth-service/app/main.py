from fastapi import FastAPI
from .database import db

app = FastAPI(title="Auth Service")

@app.on_event("startup")
async def startup_event():
    await db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()

@app.get("/health")
async def health_check():
    return {"status": "auth-service is running"}
