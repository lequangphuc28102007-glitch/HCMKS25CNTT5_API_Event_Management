"""Align existing database with current models.

Revision ID: 8f1c2d3e4a5b
Revises: 6cdde164d471
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8f1c2d3e4a5b"
down_revision: Union[str, Sequence[str], None] = "6cdde164d471"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("full_name", sa.String(255), nullable=True))
        batch_op.alter_column(
            "hashed_password",
            new_column_name="password_hash",
            existing_type=sa.String(255),
        )

    op.execute("UPDATE users SET full_name = username WHERE full_name IS NULL")

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("full_name", existing_type=sa.String(255), nullable=False)
        batch_op.drop_column("username")

    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "name", new_column_name="title", existing_type=sa.String(100)
        )
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("location", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("starts_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE events SET starts_at = created_at WHERE starts_at IS NULL")

    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column("starts_at", existing_type=sa.DateTime(), nullable=False)

    with op.batch_alter_table("event_tasks") as batch_op:
        batch_op.drop_constraint("event_tasks_ibfk_2", type_="foreignkey")
        batch_op.alter_column(
            "assigned_to",
            new_column_name="assignee_id",
            existing_type=sa.Integer(),
        )
        batch_op.create_foreign_key(
            "event_tasks_ibfk_assignee", "users", ["assignee_id"], ["id"], ondelete="SET NULL"
        )

    op.drop_table("event_staffs")


def downgrade() -> None:
    op.create_table(
        "event_staffs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("event_tasks") as batch_op:
        batch_op.drop_constraint("event_tasks_ibfk_assignee", type_="foreignkey")
        batch_op.alter_column(
            "assignee_id",
            new_column_name="assigned_to",
            existing_type=sa.Integer(),
        )
        batch_op.create_foreign_key(
            "event_tasks_ibfk_2", "event_staffs", ["assigned_to"], ["id"]
        )

    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "title", new_column_name="name", existing_type=sa.String(255)
        )
        batch_op.drop_column("description")
        batch_op.drop_column("location")
        batch_op.drop_column("starts_at")

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(50), nullable=True))
        batch_op.alter_column(
            "password_hash",
            new_column_name="hashed_password",
            existing_type=sa.String(255),
        )

    op.execute("UPDATE users SET username = full_name WHERE username IS NULL")

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("username", existing_type=sa.String(50), nullable=False)
        batch_op.drop_column("full_name")
