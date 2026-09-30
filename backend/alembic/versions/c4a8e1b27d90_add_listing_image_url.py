"""add listing image_url

Revision ID: c4a8e1b27d90
Revises: 2472d694a3d0
Create Date: 2026-09-30 17:40:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4a8e1b27d90"
down_revision: str | Sequence[str] | None = "2472d694a3d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("image_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("listings", "image_url")
