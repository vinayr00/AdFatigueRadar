"""Initial AdFatigueRadar persistence schema.

Revision ID: 0001_initial
"""
from alembic import op
from backend.db.models import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Initial schema is generated from the checked-in declarative contract.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)

def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
