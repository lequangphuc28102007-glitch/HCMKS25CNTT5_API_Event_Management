from datetime import datetime, timedelta
from app.db.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.event import Event, EventStaff, EventStaffRole
from app.models.event_task import EventTask, TaskStatus, TaskPriority
from app.core.security import hash_password


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            print("Created Admin: admin@example.com / admin123")

        # User 1 (Owner)
        user1 = db.query(User).filter_by(email="user1@example.com").first()
        if not user1:
            user1 = User(
                email="user1@example.com",
                password_hash=hash_password("user123"),
                full_name="Nguyen Van A (Owner)",
                role=UserRole.USER,
                is_active=True,
            )
            db.add(user1)
            print("Created User 1: user1@example.com / user123")

        # User 2 (Member/Staff)
        user2 = db.query(User).filter_by(email="user2@example.com").first()
        if not user2:
            user2 = User(
                email="user2@example.com",
                password_hash=hash_password("user123"),
                full_name="Tran Thi B (Staff)",
                role=UserRole.USER,
                is_active=True,
            )
            db.add(user2)
            print("Created User 2: user2@example.com / user123")

        db.commit()

        # Refresh users
        if admin:
            db.refresh(admin)
        if user1:
            db.refresh(user1)
        if user2:
            db.refresh(user2)

        # Sample Event
        event = db.query(Event).filter_by(name="Tech Conference 2026").first()
        if not event and user1 and user2:
            event = Event(
                name="Tech Conference 2026",
                description="Hội thảo công nghệ thường niên về AI và Cloud Computing.",
                owner_id=user1.id,
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            # Add Owner to EventStaff
            staff_owner = EventStaff(
                event_id=event.id,
                user_id=user1.id,
                role=EventStaffRole.OWNER,
            )
            # Add Member to EventStaff
            staff_member = EventStaff(
                event_id=event.id,
                user_id=user2.id,
                role=EventStaffRole.MEMBER,
            )
            db.add_all([staff_owner, staff_member])

            # Sample Tasks
            task1 = EventTask(
                event_id=event.id,
                title="Chuẩn bị backdrop và banner sự kiện",
                description="Thiết kế và in ấn backdrop sân khấu chính kích thước 6x3m.",
                assignee_id=user2.id,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                due_date=datetime.now() + timedelta(days=5),
            )
            task2 = EventTask(
                event_id=event.id,
                title="Gửi thư mời diễn giả và khách mời VIP",
                description="Gửi email và liên hệ xác nhận danh sách diễn giả tham dự.",
                assignee_id=user1.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.now() + timedelta(days=7),
            )
            db.add_all([task1, task2])
            db.commit()
            print("Created sample event 'Tech Conference 2026' with members and tasks.")

        print("\nSeed data completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
