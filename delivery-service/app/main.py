from fastapi import FastAPI

from .database import db
from .router import router

app = FastAPI(title="Delivery Service")

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    await db.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()


@app.get("/health")
async def health_check():
    return {"status": "delivery-service is running"}
