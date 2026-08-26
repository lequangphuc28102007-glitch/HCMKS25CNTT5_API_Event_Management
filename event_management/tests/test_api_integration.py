import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


# ============================================================================
# MODULE 1: HEALTH CHECK TESTS
# ============================================================================


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ============================================================================
# MODULE 2: AUTHENTICATION TESTS (Register & Login)
# ============================================================================


def test_auth_register_and_login_flow():
    # 1. Register new user (Happy Path)
    reg_payload = {
        "email": "user1@example.com",
        "password": "password123",
        "full_name": "  Nguyen Van A  ",  # tests stripping whitespace
    }
    res = client.post("/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "user1@example.com"
    assert data["full_name"] == "Nguyen Van A"  # stripped
    assert data["role"] == "USER"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data

    # 2. Register duplicate email (Error Case -> 400)
    res_dup = client.post("/auth/register", json=reg_payload)
    assert res_dup.status_code == 400
    assert res_dup.json()["error"] is True
    assert "Email đã được sử dụng" in res_dup.json()["message"]

    # 3. Register with blank/whitespace full_name (Error Case -> 422)
    res_blank_name = client.post(
        "/auth/register",
        json={"email": "valid@example.com", "password": "password123", "full_name": "   "},
    )
    assert res_blank_name.status_code == 422
    assert res_blank_name.json()["error"] is True

    # 4. Register invalid input (short password, invalid email) (Error Case -> 422)
    res_inv = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "123", "full_name": ""},
    )
    assert res_inv.status_code == 422

    # 5. Login success (Happy Path)
    login_res = client.post(
        "/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 6. Login wrong password (Error Case -> 401)
    login_fail = client.post(
        "/auth/login",
        json={"email": "user1@example.com", "password": "wrongpassword"},
    )
    assert login_fail.status_code == 401
    assert login_fail.json()["error"] is True

    # 7. Login non-existent email (Error Case -> 401)
    login_non_exist = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert login_non_exist.status_code == 401

    # 8. GET /users/me with token (Happy Path)
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "user1@example.com"
    assert "password_hash" not in me_data

    # 9. GET /users/me without token / bad token (Error Case -> 401)
    assert client.get("/users/me").status_code == 401
    assert (
        client.get("/users/me", headers={"Authorization": "Bearer badtoken"}).status_code
        == 401
    )


# ============================================================================
# MODULE 3: USERS MANAGEMENT & RBAC TESTS
# ============================================================================


def test_users_admin_endpoint_and_permissions():
    # Setup regular user, admin user, and inactive user in DB
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
    assert res_forbidden.json()["error"] is True

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
    assert "vô hiệu hóa" in inactive_login.json()["message"]


# ============================================================================
# MODULE 4: EVENTS CRUD & OWNERSHIP TESTS
# ============================================================================


def test_events_crud_and_ownership():
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
        json={"name": "  Hoi Thao Cong Nghe  ", "description": "Mo ta hoi thao"},
        headers=h1,
    )
    assert res_ev.status_code == 201
    event_data = res_ev.json()
    event_id = event_data["id"]
    assert event_data["name"] == "Hoi Thao Cong Nghe"  # trimmed
    assert event_data["owner_id"] == u1.id

    # 2. POST /events with blank name -> 422
    res_blank = client.post("/events", json={"name": "   "}, headers=h1)
    assert res_blank.status_code == 422

    # 3. GET /events: owner sees it, other user does not
    res_list1 = client.get("/events", headers=h1)
    assert len(res_list1.json()) == 1
    res_list2 = client.get("/events", headers=h2)
    assert len(res_list2.json()) == 0

    # 4. GET /events with search
    res_search = client.get("/events?search=Cong Nghe", headers=h1)
    assert len(res_search.json()) == 1
    res_search_empty = client.get("/events?search=Am Nhac", headers=h1)
    assert len(res_search_empty.json()) == 0

    # 5. GET /events/{id}: owner can view, other cannot (403), non-existent (404)
    assert client.get(f"/events/{event_id}", headers=h1).status_code == 200
    assert client.get(f"/events/{event_id}", headers=h2).status_code == 403
    assert client.get("/events/99999", headers=h1).status_code == 404

    # 6. PATCH /events/{id} and PUT /events/{id}
    res_patch = client.patch(
        f"/events/{event_id}", json={"name": "Hoi Thao Cap Nhat"}, headers=h1
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["name"] == "Hoi Thao Cap Nhat"
    assert res_patch.json()["description"] == "Mo ta hoi thao"

    res_put = client.put(
        f"/events/{event_id}",
        json={"name": "Hoi Thao PUT", "description": "Mo ta moi"},
        headers=h1,
    )
    assert res_put.status_code == 200
    assert res_put.json()["name"] == "Hoi Thao PUT"

    # Non-owner cannot update
    assert (
        client.patch(
            f"/events/{event_id}", json={"name": "Hack"}, headers=h2
        ).status_code
        == 403
    )

    # 7. DELETE /events/{id}
    # Non-owner cannot delete
    assert client.delete(f"/events/{event_id}", headers=h2).status_code == 403
    # Owner deletes
    assert client.delete(f"/events/{event_id}", headers=h1).status_code == 204
    # Check it is gone
    assert client.get(f"/events/{event_id}", headers=h1).status_code == 404


# ============================================================================
# MODULE 5: EVENT MEMBERS MANAGEMENT TESTS
# ============================================================================


def test_event_members_management():
    # Setup owner, member, inactive user, and outsider
    db = TestingSessionLocal()
    owner = User(
        email="owner@test.com", full_name="Owner", password_hash=hash_password("pass")
    )
    member_user = User(
        email="member@test.com",
        full_name="Member",
        password_hash=hash_password("pass"),
    )
    inactive_user = User(
        email="inactive_m@test.com",
        full_name="Inactive Member",
        password_hash=hash_password("pass"),
        is_active=False,
    )
    outsider = User(
        email="outsider@test.com",
        full_name="Outsider",
        password_hash=hash_password("pass"),
    )
    db.add_all([owner, member_user, inactive_user, outsider])
    db.commit()
    db.refresh(owner)
    db.refresh(member_user)
    db.refresh(inactive_user)
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

    # 1. Owner adds member (Happy Path -> 201)
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

    # 4. Add inactive user -> 400
    res_add_inactive = client.post(
        f"/events/{ev_id}/members", json={"user_id": inactive_user.id}, headers=h_owner
    )
    assert res_add_inactive.status_code == 400
    assert "vô hiệu hóa" in res_add_inactive.json()["message"]

    # 5. Non-owner cannot add member -> 403
    assert (
        client.post(
            f"/events/{ev_id}/members",
            json={"user_id": outsider.id},
            headers=h_member,
        ).status_code
        == 403
    )

    # 6. GET /events/{id}/members
    # Member can view
    members_res = client.get(f"/events/{ev_id}/members", headers=h_member)
    assert members_res.status_code == 200
    assert len(members_res.json()) == 2
    # Outsider cannot view
    assert (
        client.get(f"/events/{ev_id}/members", headers=h_outsider).status_code == 403
    )

    # 7. DELETE /events/{id}/members/{user_id}
    # Non-owner cannot remove
    assert (
        client.delete(
            f"/events/{ev_id}/members/{member_user.id}", headers=h_member
        ).status_code
        == 403
    )
    # Owner cannot remove the owner -> 400
    assert (
        client.delete(
            f"/events/{ev_id}/members/{owner.id}", headers=h_owner
        ).status_code
        == 400
    )
    # Remove non-existent member -> 404
    assert (
        client.delete(
            f"/events/{ev_id}/members/99999", headers=h_owner
        ).status_code
        == 404
    )
    # Owner removes member -> 204
    assert (
        client.delete(
            f"/events/{ev_id}/members/{member_user.id}", headers=h_owner
        ).status_code
        == 204
    )
    # Member is now removed
    assert len(client.get(f"/events/{ev_id}/members", headers=h_owner).json()) == 1


# ============================================================================
# MODULE 6: EVENT TASKS FULL FLOW & EDGE CASES TESTS
# ============================================================================


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

    # 2. Staff1 creates task assigned to Staff1 (Happy Path -> 201)
    res_create_t1 = client.post(
        f"/events/{ev_id}/event-tasks",
        json={
            "title": "  Chuan bi am thanh  ",
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
    assert t1_data["title"] == "Chuan bi am thanh"  # stripped
    assert t1_data["status"] == "TODO"
    assert t1_data["priority"] == "HIGH"
    assert t1_data["assignee_id"] == staff1.id

    # 3. Create another task (assigned to Staff2)
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

    # 4. Create unassigned task (assignee_id = None)
    res_create_unassigned = client.post(
        f"/events/{ev_id}/event-tasks",
        json={"title": "Task chua giao", "description": "Cho phan cong"},
        headers=h_owner,
    )
    assert res_create_unassigned.status_code == 201
    assert res_create_unassigned.json()["assignee_id"] is None

    # 5. Outsider cannot create task -> 403
    assert (
        client.post(
            f"/events/{ev_id}/event-tasks",
            json={"title": "Hack"},
            headers=h_outsider,
        ).status_code
        == 403
    )

    # 6. GET /events/{id}/event-tasks with filters, case-insensitive sort & pagination
    res_list = client.get(
        f"/events/{ev_id}/event-tasks?page=1&size=10&sort_by=created_at&sort_order=DESC",
        headers=h_staff1,
    )
    assert res_list.status_code == 200
    paginated = res_list.json()
    assert paginated["total"] == 3
    assert len(paginated["items"]) == 3

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

    # 7. GET /event-tasks/{task_id}
    # Member can view
    assert client.get(f"/event-tasks/{t1_id}", headers=h_staff2).status_code == 200
    # Outsider cannot view (403)
    assert client.get(f"/event-tasks/{t1_id}", headers=h_outsider).status_code == 403
    # Non-existent task (404)
    assert client.get("/event-tasks/99999", headers=h_staff1).status_code == 404

    # 8. PATCH & PUT /event-tasks/{task_id}
    # Staff1 (assignee) updates status via PATCH
    patch_res = client.patch(
        f"/event-tasks/{t1_id}",
        json={"status": "IN_PROGRESS"},
        headers=h_staff1,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "IN_PROGRESS"
    assert patch_res.json()["title"] == "Chuan bi am thanh"

    # Staff1 updates via PUT
    put_res = client.put(
        f"/event-tasks/{t1_id}",
        json={"title": "Chuan bi loa đai", "priority": "HIGH"},
        headers=h_staff1,
    )
    assert put_res.status_code == 200
    assert put_res.json()["title"] == "Chuan bi loa đai"

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

    # Assigning to outsider via PATCH -> 400
    assert (
        client.patch(
            f"/event-tasks/{t1_id}",
            json={"assignee_id": outsider.id},
            headers=h_owner,
        ).status_code
        == 400
    )

    # Unassigning task via assignee_id: null -> 200
    unassign_res = client.patch(
        f"/event-tasks/{t1_id}",
        json={"assignee_id": None},
        headers=h_owner,
    )
    assert unassign_res.status_code == 200
    assert unassign_res.json()["assignee_id"] is None

    # Re-assign back to Staff1
    client.patch(
        f"/event-tasks/{t1_id}",
        json={"assignee_id": staff1.id},
        headers=h_owner,
    )

    # 9. Verify removing a member unassigns their tasks in that event
    # Remove staff1
    del_mem_res = client.delete(f"/events/{ev_id}/members/{staff1.id}", headers=h_owner)
    assert del_mem_res.status_code == 204
    # Check t1 assignee_id is now None (unassigned)
    t1_check = client.get(f"/event-tasks/{t1_id}", headers=h_owner).json()
    assert t1_check["assignee_id"] is None

    # 10. DELETE /event-tasks/{task_id}
    # Outsider tries to delete -> 403
    assert client.delete(f"/event-tasks/{t2_id}", headers=h_outsider).status_code == 403
    # Staff2 (assignee of t2) can delete t2 -> 204
    assert client.delete(f"/event-tasks/{t2_id}", headers=h_staff2).status_code == 204
    # Check it is deleted
    assert client.get(f"/event-tasks/{t2_id}", headers=h_owner).status_code == 404


# ============================================================================
# MODULE 7: ERROR HANDLING STRUCTURE & 404/405/422 TESTS
# ============================================================================


def test_error_handling_structure():
    # 1. Non-existent route -> Starlette 404 with structured error JSON
    res_404 = client.get("/api/non-existent-endpoint")
    assert res_404.status_code == 404
    assert res_404.json()["error"] is True

    # 2. Method Not Allowed -> Starlette 405 with structured error JSON
    res_405 = client.delete("/auth/login")
    assert res_405.status_code == 405
    assert res_405.json()["error"] is True

    # 3. Validation error on invalid body -> 422 with structured detail
    res_422 = client.post("/auth/register", json={"email": "invalid"})
    assert res_422.status_code == 422
    assert res_422.json()["error"] is True
    assert "detail" in res_422.json()

