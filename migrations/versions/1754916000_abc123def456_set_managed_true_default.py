"""Set managed=True as default for new groups and update existing groups

Revision ID: abc123def456
Revises: bbba88e22126
Create Date: 2025-08-11 15:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "abc123def456"
down_revision: Union[str, None] = "bbba88e22126"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing groups to set managed=True
    op.execute("UPDATE \"group\" SET managed = true WHERE managed = false")
    
    # Update the column default for new groups
    op.alter_column(
        "group",
        "managed",
        server_default=sa.text("true"),
        existing_type=sa.Boolean(),
        existing_nullable=False
    )


def downgrade() -> None:
    # Revert the column default
    op.alter_column(
        "group",
        "managed", 
        server_default=sa.text("false"),
        existing_type=sa.Boolean(),
        existing_nullable=False
    )
    
    # Note: We don't revert the data changes as that would disable management
    # for groups that may now be actively managed