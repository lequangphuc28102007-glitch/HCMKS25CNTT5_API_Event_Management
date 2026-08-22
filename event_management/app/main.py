from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.db.database import Base, engine
from app.models import event, user
from app.routers import auth, event as event_router, event_task as event_task_router, users

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=os.getenv("APP_TITLE", "Event Management API"),
    version=os.getenv("APP_VERSION", "0.1.0")
)

# Đăng ký router
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(event_router.router)
app.include_router(event_task_router.router)

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
