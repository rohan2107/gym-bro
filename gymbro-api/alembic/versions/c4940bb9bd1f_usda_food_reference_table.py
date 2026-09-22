"""usda food reference table

Loads data/usda_foods.json (built by scripts/build_usda_dataset.py from USDA FoodData
Central's public-domain bulk downloads; see docs/adr/0010-usda-as-a-local-reference.md) into
a new usda_food table, so nutrition lookup queries this database instead of calling USDA's
search API on every request.

This is reference data the app ships with, not user data: the whole table is repopulated by
downgrading and upgrading again, which is expected and safe.

Revision ID: c4940bb9bd1f
Revises: 573ff5ce6812
Create Date: 2026-09-22 15:00:00.000000

"""
import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c4940bb9bd1f'
down_revision: Union[str, None] = '573ff5ce6812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# gymbro-api/alembic/versions/<this file> -> gymbro-api/data/usda_foods.json
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "usda_foods.json"
INSERT_BATCH_SIZE = 1000


def upgrade() -> None:
    op.create_table(
        'usda_food',
        sa.Column('fdc_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('data_type', sa.String(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('protein_g', sa.Float(), nullable=False),
        sa.Column('carbs_g', sa.Float(), nullable=False),
        sa.Column('fat_g', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('fdc_id'),
    )
    op.create_index('ix_usda_food_name', 'usda_food', ['name'], unique=False)

    foods = json.loads(DATA_PATH.read_text())["foods"]
    table = sa.table(
        'usda_food',
        sa.column('fdc_id', sa.Integer()),
        sa.column('name', sa.String()),
        sa.column('data_type', sa.String()),
        sa.column('calories', sa.Float()),
        sa.column('protein_g', sa.Float()),
        sa.column('carbs_g', sa.Float()),
        sa.column('fat_g', sa.Float()),
    )
    for start in range(0, len(foods), INSERT_BATCH_SIZE):
        op.bulk_insert(table, foods[start : start + INSERT_BATCH_SIZE])


def downgrade() -> None:
    op.drop_index('ix_usda_food_name', table_name='usda_food')
    op.drop_table('usda_food')
