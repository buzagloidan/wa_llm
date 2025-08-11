"""Enable spam detection by default for all groups

Revision ID: def456ghi789
Revises: abc123def456
Create Date: 2025-08-11 16:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "def456ghi789"
down_revision: Union[str, None] = "abc123def456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing groups to enable spam detection
    op.execute("UPDATE \"group\" SET notify_on_spam = true WHERE notify_on_spam = false")
    
    # Update the column default for new groups
    op.alter_column(
        "group",
        "notify_on_spam",
        server_default=sa.text("true"),
        existing_type=sa.Boolean(),
        existing_nullable=False
    )


def downgrade() -> None:
    # Revert the column default
    op.alter_column(
        "group",
        "notify_on_spam", 
        server_default=sa.text("false"),
        existing_type=sa.Boolean(),
        existing_nullable=False
    )
    
    # Note: We don't revert the data changes as groups may now rely on spam detection