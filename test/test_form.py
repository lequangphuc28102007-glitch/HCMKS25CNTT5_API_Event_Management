from fastapi import FastAPI, Form, Path

app = FastAPI()

@app.post("/events/{event_id}/members")
def add_member(
    event_id: int = Path(...),
    user_id: int = Form(...)
):
    return {"event_id": event_id, "user_id": user_id}