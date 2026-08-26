# Event Management API

RESTful API backend được xây dựng bằng **FastAPI**, hỗ trợ quản lý tài khoản người dùng, phân quyền (Admin / User), sự kiện (Events), thành viên sự kiện (Event Members) và công việc trong sự kiện (Event Tasks).

---

## 🛠 Công nghệ sử dụng

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database & ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (hỗ trợ MySQL, SQLite, PostgreSQL)
- **Database Migration**: [Alembic](https://alembic.sqlalchemy.org/)
- **Authentication**: JWT (JSON Web Token) qua `python-jose` & `passlib` (Bcrypt)
- **Validation & Settings**: `Pydantic v2` & `pydantic-settings`
- **Testing**: `pytest` & `httpx` (FastAPI TestClient)

---

## 🚀 Cài đặt & Khởi chạy (Setup)

### 1. Di chuyển vào thư mục dự án & tạo môi trường ảo

```powershell
cd event_management
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Cài đặt các thư viện phụ thuộc

```powershell
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường

Sao chép file `.env.example` thành `.env` và điều chỉnh các thông số phù hợp:

```powershell
copy .env.example .env
```

Nội dung cấu hình trong file `.env`:
```ini
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/mydb
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Lưu ý**: Nếu chưa cấu hình MySQL, bạn có thể tạm thời đổi `DATABASE_URL=sqlite:///./app.db` để chạy thử nghiệm nhanh với SQLite.

### 4. Khởi tạo Database & Dữ liệu mẫu (Seed Data)

Chạy script sau để tự động khởi tạo các bảng và nạp dữ liệu mẫu (Admin, Users, Event mẫu & Tasks mẫu):

```powershell
python seed.py
```

### 5. Khởi chạy Server

```powershell
uvicorn app.main:app --reload
```

Server sẽ chạy tại `http://127.0.0.1:8000`.

---

## 📖 Tài liệu API tương tác (Interactive API Docs)

Sau khi khởi chạy ứng dụng, bạn có thể truy cập:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 👥 Tài khoản mẫu (Seed Accounts)

Dữ liệu được nạp sẵn từ lệnh `python seed.py`:

| Email | Mật khẩu | Quyền (Role) | Mô tả / Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| `admin@example.com` | `admin123` | **ADMIN** | Quản trị hệ thống, có quyền xem danh sách toàn bộ người dùng (`GET /users`) |
| `user1@example.com` | `user123` | **USER** | Chủ sự kiện (**OWNER**) của sự kiện mẫu *"Tech Conference 2026"* |
| `user2@example.com` | `user123` | **USER** | Thành viên (**MEMBER**) và người được giao việc trong *"Tech Conference 2026"* |

---

## 🔐 Xác thực & Phân quyền (Authentication & Authorization)

Hệ thống sử dụng cơ chế xác thực qua **Bearer Token (JWT)**:
1. Gửi request `POST /auth/login` với email & password để nhận `access_token`.
2. Gắn token vào Header trong các request tiếp theo:
   ```http
   Authorization: Bearer <your_access_token>
   ```

### Phân cấp quyền:
- **Public**: Không yêu cầu đăng nhập (`/auth/register`, `/auth/login`, `/health`).
- **Authenticated User**: Mọi người dùng đã đăng nhập.
- **Admin**: Chỉ tài khoản có `role = "ADMIN"`.
- **Event Owner**: Người tạo sự kiện hoặc có vai trò `OWNER` trong sự kiện (có toàn quyền sửa, xóa sự kiện, thêm/xóa thành viên, quản lý mọi task).
- **Event Member**: Người tham gia sự kiện có vai trò `MEMBER` (có quyền xem sự kiện, xem thành viên, tạo công việc và cập nhật công việc được phân công).

---

## 📡 Danh sách API Endpoints

### 1. Authentication (Xác thực)
| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Public | Đăng ký tài khoản mới |
| `POST` | `/auth/login` | Public | Đăng nhập lấy JWT Access Token |

### 2. Users (Người dùng)
| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/users/me` | Authenticated | Xem thông tin hồ sơ của người dùng hiện tại |
| `GET` | `/users` | Admin | Tìm kiếm & xem danh sách người dùng (lọc theo keyword, is_active) |

### 3. Events (Sự kiện)
| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `POST` | `/events` | Authenticated | Tạo sự kiện mới (người tạo tự động là OWNER) |
| `GET` | `/events` | Authenticated | Lấy danh sách sự kiện của tôi (tham gia hoặc sở hữu, có search) |
| `GET` | `/events/{event_id}` | Event Member/Owner | Xem chi tiết sự kiện |
| `PATCH` | `/events/{event_id}` | Event Owner | Cập nhật một phần thông tin sự kiện |
| `PUT` | `/events/{event_id}` | Event Owner | Cập nhật toàn bộ thông tin sự kiện |
| `DELETE` | `/events/{event_id}` | Event Owner | Xóa sự kiện |

### 4. Event Members (Thành viên sự kiện)
| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `POST` | `/events/{event_id}/members` | Event Owner | Thêm người dùng vào sự kiện |
| `GET` | `/events/{event_id}/members` | Event Member/Owner | Xem danh sách thành viên trong sự kiện |
| `DELETE` | `/events/{event_id}/members/{user_id}`| Event Owner | Xóa thành viên khỏi sự kiện |

### 5. Event Tasks (Công việc sự kiện)
| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `POST` | `/events/{event_id}/event-tasks` | Event Member/Owner | Tạo công việc mới cho sự kiện |
| `GET` | `/events/{event_id}/event-tasks` | Event Member/Owner | Danh sách công việc (hỗ trợ search, filter status/priority/assignee, sort, pagination) |
| `GET` | `/event-tasks/{task_id}` | Event Member/Owner | Xem chi tiết một công việc |
| `PATCH` | `/event-tasks/{task_id}` | Event Owner / Assignee | Cập nhật trạng thái / thông tin công việc |
| `DELETE` | `/event-tasks/{task_id}` | Event Owner / Assignee | Xóa công việc |

### 6. System Health
| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Kiểm tra trạng thái hoạt động của hệ thống |

---

## 🧪 Chạy Kiểm thử (Testing)

Dự án có sẵn bộ test tích hợp (Integration Tests) bao phủ các luồng: Auth, Users, Events, Staff, Tasks và Health check.

Chạy test bằng lệnh:

```powershell
python -m pytest
```

---

## 🗂 Cấu trúc thư mục (Project Structure)

```text
event_management/
├── app/
│   ├── core/                  # Cấu hình app, bảo mật JWT, xử lý ngoại lệ
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── db/                    # Kết nối Database & Base Model
│   │   └── database.py
│   ├── dependencies/          # Dependency injection (Auth, Permissions)
│   │   ├── auth.py
│   │   └── permissions.py
│   ├── models/                # SQLAlchemy Models (User, Event, EventStaff, EventTask)
│   ├── routers/               # API Router endpoints
│   │   ├── auth.py
│   │   ├── event.py
│   │   ├── event_task.py
│   │   └── users.py
│   ├── schemas/               # Pydantic Schemas (Request / Response validation)
│   ├── services/              # Business Logic Layer
│   └── main.py                # Điểm khởi tạo FastAPI Application
├── migrations/                # Alembic migration scripts
├── tests/                     # Integration tests
│   ├── test_api_integration.py
│   └── test_health.py
├── .env.example               # Mẫu biến môi trường
├── alembic.ini                # Cấu hình Alembic
├── requirements.txt           # Danh sách thư viện Python
├── seed.py                    # Script nạp dữ liệu mẫu
└── README.md                  # Hướng dẫn dự án
```
