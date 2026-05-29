${imports if imports else ""}
"""${message}"""

from alembic import op
import sqlalchemy as sa


${down_revision}
${branch_labels}
${depends_on}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}

