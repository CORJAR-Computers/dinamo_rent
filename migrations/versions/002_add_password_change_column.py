"""Add password change column

Revision ID: 002_add_password_change_column
Revises: 001_f1a
Create Date: 2026-04-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_add_password_change_column"
down_revision = "001_f1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adds the `debe_cambiar_password` column to the `usuarios` table.
    This column is a boolean flag to indicate if a user must change their password on next login.
    It defaults to FALSE for all existing users.
    """
    op.add_column(
        "usuarios",
        sa.Column(
            "debe_cambiar_password", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
    )


def downgrade() -> None:
    """
    Removes the `debe_cambiar_password` column from the `usuarios` table.
    """
    op.drop_column("usuarios", "debe_cambiar_password")
