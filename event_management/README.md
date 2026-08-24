# Event Management API

FastAPI starter project for user accounts, events, event staff, and event tasks.

## Setup

```powershell
cd event_management
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Run

```powershell
uvicorn app.main:app --reload
```

Apply database migrations before the first run:

```powershell
alembic upgrade head
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## Endpoints

- `POST /auth/register` - create an account
- `POST /auth/login` - get a bearer token (OAuth2 form)
- `GET /users/me` - current user
- `GET|POST /events` - list or create owned events
- `GET|POST /events/{event_id}/tasks` - list or create event tasks
- `GET /health` - service health check
