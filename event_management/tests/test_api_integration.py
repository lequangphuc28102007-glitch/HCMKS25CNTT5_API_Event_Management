import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.db.database import Base, get_db
from app.main import app
from app.models.event import Event, EventStaff, EventStaffRole
from app.models.event_task import EventTask, TaskPriority, TaskStatus
from app.models.user import User, UserRole

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_register_and_login_flow():
    # 1. Register new user
    reg_payload = {
        "email": "user1@example.com",
        "password": "password123",
        "full_name": "Nguyen Van A",
    }
    res = client.post("/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "user1@example.com"
    assert data["full_name"] == "Nguyen Van A"
    assert data["role"] == "USER"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data

    # 2. Register duplicate email
    res_dup = client.post("/auth/register", json=reg_payload)
    assert res_dup.status_code == 400
    assert res_dup.json()["error"] is True

    # 3. Register invalid input (short password, invalid email)
    res_inv = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "123", "full_name": ""},
    )
    assert res_inv.status_code == 422

    # 4. Login success
    login_res = client.post(
        "/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 5. Login wrong password
    login_fail = client.post(
        "/auth/login",
        json={"email": "user1@example.com", "password": "wrongpassword"},
    )
    assert login_fail.status_code == 401

    # 6. GET /users/me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "user1@example.com"
    assert "password_hash" not in me_data

    # 7. GET /users/me without token / bad token
    assert client.get("/users/me").status_code == 401
    assert (
        client.get("/users/me", headers={"Authorization": "Bearer badtoken"}).status_code
        == 401
    )


def test_users_admin_endpoint_and_permissions():
    # Create regular user and admin user directly in DB
    db = TestingSessionLocal()
    user = User(
        email="regular@example.com",
        full_name="Regular User",
        password_hash=hash_password("password123"),
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        password_hash=hash_password("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    inactive_user = User(
        email="inactive@example.com",
        full_name="Inactive User",
        password_hash=hash_password("password123"),
        role=UserRole.USER,
        is_active=False,
    )
    db.add_all([user, admin, inactive_user])
    db.commit()
    db.refresh(user)
    db.refresh(admin)
    db.refresh(inactive_user)
    db.close()

    # Login as regular user
    user_token = client.post(
        "/auth/login", json={"email": "regular@example.com", "password": "password123"}
    ).json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Login as admin
    admin_token = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "password123"}
    ).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Regular user calls GET /users -> 403 Forbidden
    res_forbidden = client.get("/users", headers=user_headers)
    assert res_forbidden.status_code == 403

    # Admin calls GET /users -> 200 OK
    res_admin = client.get("/users", headers=admin_headers)
    assert res_admin.status_code == 200
    users_list = res_admin.json()
    assert len(users_list) == 3

    # Admin searches keyword
    res_search = client.get("/users?keyword=Admin", headers=admin_headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["email"] == "admin@example.com"

    # Admin filters is_active=false
    res_filter = client.get("/users?is_active=false", headers=admin_headers)
    assert res_filter.status_code == 200
    assert len(res_filter.json()) == 1
    assert res_filter.json()[0]["email"] == "inactive@example.com"

    # Inactive user login fails with 401
    inactive_login = client.post(
        "/auth/login", json={"email": "inactive@example.com", "password": "password123"}
    )
    assert inactive_login.status_code == 401


def test_events_crud_and_ownership():
    # Create 2 users
    db = TestingSessionLocal()
    u1 = User(
        email="owner@example.com",
        full_name="Owner",
        password_hash=hash_password("pass123"),
    )
    u2 = User(
        email="other@example.com",
        full_name="Other",
        password_hash=hash_password("pass123"),
    )
    db.add_all([u1, u2])
    db.commit()
    db.refresh(u1)
    db.refresh(u2)
    db.close()

    t1 = client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "pass123"}
    ).json()["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    t2 = client.post(
        "/auth/login", json={"email": "other@example.com", "password": "pass123"}
    ).json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    # 1. POST /events -> created, user becomes owner
    res_ev = client.post(
        "/events",
        json={"name": "Hoi Thao Cong Nghe", "description": "Mo ta hoi thao"},
        headers=h1,
    )
    assert res_ev.status_code == 201
    event_data = res_ev.json()
    event_id = event_data["id"]
    assert event_data["name"] == "Hoi Thao Cong Nghe"
    assert event_data["owner_id"] == u1.id

    # 2. GET /events: owner sees it, other user does not
    res_list1 = client.get("/events", headers=h1)
    assert len(res_list1.json()) == 1
    res_list2 = client.get("/events", headers=h2)
    assert len(res_list2.json()) == 0

    # 3. GET /events with search
    res_search = client.get("/events?search=Cong Nghe", headers=h1)
    assert len(res_search.json()) == 1
    res_search_empty = client.get("/events?search=Am Nhac", headers=h1)
    assert len(res_search_empty.json()) == 0

    # 4. GET /events/{id}: owner can view, other cannot (403)
    assert client.get(f"/events/{event_id}", headers=h1).status_code == 200
    assert client.get(f"/events/{event_id}", headers=h2).status_code == 403
    assert client.get("/events/99999", headers=h1).status_code == 404

    # 5. PATCH /events/{id} and PUT /events/{id}
    res_patch = client.patch(
        f"/events/{event_id}", json={"name": "Hoi Thao Cap Nhat"}, headers=h1
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["name"] == "Hoi Thao Cap Nhat"
    assert res_patch.json()["description"] == "Mo ta hoi thao"

    # Non-owner cannot update
    assert (
        client.patch(
            f"/events/{event_id}", json={"name": "Hack"}, headers=h2
        ).status_code
        == 403
    )

    # 6. DELETE /events/{id}
    # Non-owner cannot delete
    assert client.delete(f"/events/{event_id}", headers=h2).status_code == 403
    # Owner deletes
    assert client.delete(f"/events/{event_id}", headers=h1).status_code == 204
    # Check it is gone
    assert client.get(f"/events/{event_id}", headers=h1).status_code == 404


def test_event_members_management():
    # Setup owner, member, and outsider
    db = TestingSessionLocal()
    owner = User(
        email="owner@test.com", full_name="Owner", password_hash=hash_password("pass")
    )
    member_user = User(
        email="member@test.com",
        full_name="Member",
        password_hash=hash_password("pass"),
    )
    outsider = User(
        email="outsider@test.com",
        full_name="Outsider",
        password_hash=hash_password("pass"),
    )
    db.add_all([owner, member_user, outsider])
    db.commit()
    db.refresh(owner)
    db.refresh(member_user)
    db.refresh(outsider)
    db.close()

    h_owner = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'owner@test.com', 'password': 'pass'}).json()['access_token']}"
    }
    h_member = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'member@test.com', 'password': 'pass'}).json()['access_token']}"
    }
    h_outsider = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'outsider@test.com', 'password': 'pass'}).json()['access_token']}"
    }

    # Create event
    ev_id = client.post("/events", json={"name": "Event A"}, headers=h_owner).json()["id"]

    # 1. Owner adds member
    add_res = client.post(
        f"/events/{ev_id}/members", json={"user_id": member_user.id}, headers=h_owner
    )
    assert add_res.status_code == 201
    assert add_res.json()["user_id"] == member_user.id
    assert add_res.json()["role"] == "MEMBER"
    assert add_res.json()["user"]["email"] == "member@test.com"

    # 2. Add duplicate member -> 400
    assert (
        client.post(
            f"/events/{ev_id}/members",
            json={"user_id": member_user.id},
            headers=h_owner,
        ).status_code
        == 400
    )

    # 3. Add non-existent user -> 404
    assert (
        client.post(
            f"/events/{ev_id}/members", json={"user_id": 99999}, headers=h_owner
        ).status_code
        == 404
    )

    # 4. Non-owner cannot add member -> 403
    assert (
        client.post(
            f"/events/{ev_id}/members",
            json={"user_id": outsider.id},
            headers=h_member,
        ).status_code
        == 403
    )

    # 5. GET /events/{id}/members
    # Member can view
    members_res = client.get(f"/events/{ev_id}/members", headers=h_member)
    assert members_res.status_code == 200
    assert len(members_res.json()) == 2
    # Outsider cannot view
    assert (
        client.get(f"/events/{ev_id}/members", headers=h_outsider).status_code == 403
    )

    # 6. DELETE /events/{id}/members/{user_id}
    # Non-owner cannot remove
    assert (
        client.delete(
            f"/events/{ev_id}/members/{member_user.id}", headers=h_member
        ).status_code
        == 403
    )
    # Owner cannot remove the owner
    assert (
        client.delete(
            f"/events/{ev_id}/members/{owner.id}", headers=h_owner
        ).status_code
        == 400
    )
    # Owner removes member
    assert (
        client.delete(
            f"/events/{ev_id}/members/{member_user.id}", headers=h_owner
        ).status_code
        == 204
    )
    # Member is now removed
    assert len(client.get(f"/events/{ev_id}/members", headers=h_owner).json()) == 1


def test_event_tasks_full_flow():
    # Setup users
    db = TestingSessionLocal()
    owner = User(
        email="owner_t@test.com", full_name="Owner T", password_hash=hash_password("pass")
    )
    staff1 = User(
        email="staff1@test.com", full_name="Staff 1", password_hash=hash_password("pass")
    )
    staff2 = User(
        email="staff2@test.com", full_name="Staff 2", password_hash=hash_password("pass")
    )
    outsider = User(
        email="outsider_t@test.com",
        full_name="Outsider T",
        password_hash=hash_password("pass"),
    )
    db.add_all([owner, staff1, staff2, outsider])
    db.commit()
    db.refresh(owner)
    db.refresh(staff1)
    db.refresh(staff2)
    db.refresh(outsider)
    db.close()

    h_owner = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'owner_t@test.com', 'password': 'pass'}).json()['access_token']}"
    }
    h_staff1 = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'staff1@test.com', 'password': 'pass'}).json()['access_token']}"
    }
    h_staff2 = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'staff2@test.com', 'password': 'pass'}).json()['access_token']}"
    }
    h_outsider = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'email': 'outsider_t@test.com', 'password': 'pass'}).json()['access_token']}"
    }

    # Create event and add staff1 and staff2
    ev_id = client.post("/events", json={"name": "Event Task Test"}, headers=h_owner).json()["id"]
    client.post(
        f"/events/{ev_id}/members", json={"user_id": staff1.id}, headers=h_owner
    )
    client.post(
        f"/events/{ev_id}/members", json={"user_id": staff2.id}, headers=h_owner
    )

    # 1. Create task with assignee outside event -> 400
    res_assign_outsider = client.post(
        f"/events/{ev_id}/event-tasks",
        json={
            "title": "Task 1",
            "description": "Desc 1",
            "priority": "HIGH",
            "assignee_id": outsider.id,
        },
        headers=h_owner,
    )
    assert res_assign_outsider.status_code == 400

    # 2. Staff1 creates task assigned to Staff1
    res_create_t1 = client.post(
        f"/events/{ev_id}/event-tasks",
        json={
            "title": "Chuan bi am thanh",
            "description": "Kiem tra loa mic",
            "priority": "HIGH",
            "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "assignee_id": staff1.id,
        },
        headers=h_staff1,
    )
    assert res_create_t1.status_code == 201
    t1_data = res_create_t1.json()
    t1_id = t1_data["id"]
    assert t1_data["status"] == "TODO"
    assert t1_data["priority"] == "HIGH"
    assert t1_data["assignee_id"] == staff1.id

    # 3. Create another task
    res_create_t2 = client.post(
        f"/events/{ev_id}/event-tasks",
        json={
            "title": "Chuan bi san khau",
            "description": "Trang tri backdrop",
            "priority": "LOW",
            "assignee_id": staff2.id,
        },
        headers=h_owner,
    )
    assert res_create_t2.status_code == 201
    t2_id = res_create_t2.json()["id"]

    # 4. Outsider cannot create task -> 403
    assert (
        client.post(
            f"/events/{ev_id}/event-tasks",
            json={"title": "Hack"},
            headers=h_outsider,
        ).status_code
        == 403
    )

    # 5. GET /events/{id}/event-tasks with filters & pagination
    res_list = client.get(
        f"/events/{ev_id}/event-tasks?page=1&size=10", headers=h_staff1
    )
    assert res_list.status_code == 200
    paginated = res_list.json()
    assert paginated["total"] == 2
    assert len(paginated["items"]) == 2

    # Filter by priority
    res_filter_p = client.get(
        f"/events/{ev_id}/event-tasks?priority=HIGH", headers=h_staff1
    )
    assert res_filter_p.json()["total"] == 1
    assert res_filter_p.json()["items"][0]["title"] == "Chuan bi am thanh"

    # Filter by search
    res_search = client.get(
        f"/events/{ev_id}/event-tasks?search=san khau", headers=h_staff1
    )
    assert res_search.json()["total"] == 1

    # Filter by assignee
    res_assignee_filter = client.get(
        f"/events/{ev_id}/event-tasks?assignee_id={staff2.id}", headers=h_staff1
    )
    assert res_assignee_filter.json()["total"] == 1

    # 6. GET /event-tasks/{task_id}
    # Member can view
    assert client.get(f"/event-tasks/{t1_id}", headers=h_staff2).status_code == 200
    # Outsider cannot view (403)
    assert client.get(f"/event-tasks/{t1_id}", headers=h_outsider).status_code == 403
    # Non-existent task (404)
    assert client.get("/event-tasks/99999", headers=h_staff1).status_code == 404

    # 7. PATCH /event-tasks/{task_id}
    # Staff1 (assignee) updates status
    patch_res = client.patch(
        f"/event-tasks/{t1_id}",
        json={"status": "IN_PROGRESS"},
        headers=h_staff1,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "IN_PROGRESS"
    assert patch_res.json()["title"] == "Chuan bi am thanh"  # not overwritten

    # Staff2 (other member, not owner, not assignee) tries to modify t1 -> 403
    assert (
        client.patch(
            f"/event-tasks/{t1_id}",
            json={"status": "DONE"},
            headers=h_staff2,
        ).status_code
        == 403
    )

    # Owner can modify any task
    patch_owner = client.patch(
        f"/event-tasks/{t1_id}",
        json={"status": "DONE"},
        headers=h_owner,
    )
    assert patch_owner.status_code == 200
    assert patch_owner.json()["status"] == "DONE"

    # 8. DELETE /event-tasks/{task_id}
    # Staff2 tries to delete t1 -> 403
    assert client.delete(f"/event-tasks/{t1_id}", headers=h_staff2).status_code == 403
    # Staff1 (assignee) can delete t1 -> 204
    assert client.delete(f"/event-tasks/{t1_id}", headers=h_staff1).status_code == 204
    # Check it is deleted
    assert client.get(f"/event-tasks/{t1_id}", headers=h_owner).status_code == 404
