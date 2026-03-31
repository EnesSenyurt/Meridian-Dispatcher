from fastapi import FastAPI
from .database import db

app = FastAPI(title="Tracking Service")

from .router import router as tracking_router
app.include_router(tracking_router)

@app.on_event("startup")
async def startup_event():
    await db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()

@app.get("/health")
async def health_check():
    return {"status": "tracking-service is running"}
