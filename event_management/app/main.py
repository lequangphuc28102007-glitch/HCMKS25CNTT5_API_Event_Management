from fastapi import FastAPI

from app.db.database import Base, engine
from app.models import event, user
from app.routers import auth, event as event_router, event_task as event_task_router, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Management API", version="0.1.0")
app.include_router(auth.router)
app.include_router(users.router)
# app.include_router(event_router.router)
# app.include_router(event_task_router.router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
