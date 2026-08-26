from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.db.database import Base, engine
from app.models import Event, EventStaff, EventTask, User  
from app.routers import auth, event, event_task, users

app = FastAPI(
    title="Event Management API",
    description="API quản lý sự kiện: user, event, thành viên sự kiện, công việc sự kiện.",
    version="1.0.0",
)

register_exception_handlers(app)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(event.router)
app.include_router(event_task.router)


@app.get("/health", tags=["Health"], summary="Health check")
def health_check():
    return {"status": "ok"}
