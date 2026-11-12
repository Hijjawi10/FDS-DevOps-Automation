
"""create users table

Revision ID: 53db8c1ca5f1
Revises: 15f054a29f97
Create Date: 2026-11-12 12:22:51.760828

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = "53db8c1ca5f1"

down_revision: Union[str, Sequence[str], None] = (
    "15f054a29f97"
)

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "users",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "username",
            sa.String(length=50),
            nullable=False
        ),

        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "hashed_password",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="user"
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true")
        ),

        sa.CheckConstraint(
            "role IN ('admin', 'user')",
            name="check_user_role"
        ),

        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
        unique=False
    )

    op.create_index(
        "ix_users_username",
        "users",
        ["username"],
        unique=True
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True
    )


def downgrade() -> None:

    op.drop_index(
        "ix_users_email",
        table_name="users"
    )

    op.drop_index(
        "ix_users_username",
        table_name="users"
    )

    op.drop_index(
        "ix_users_id",
        table_name="users"
    )

    op.drop_table("users")
