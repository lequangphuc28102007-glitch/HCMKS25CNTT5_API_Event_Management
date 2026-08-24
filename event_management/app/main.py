from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.routers import auth, event as event_router, event_task as event_task_router, users, event_staff as event_staff_router

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_TITLE", "Event Management API"),
    version=os.getenv("APP_VERSION", "0.1.0")
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(event_router.router)
app.include_router(event_task_router.router)
app.include_router(event_staff_router.router)

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
