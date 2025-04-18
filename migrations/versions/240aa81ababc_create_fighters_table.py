"""Create fighters table

Revision ID: 240aa81ababc
Revises: dfa8f3833177
Create Date: 2025-04-08 18:44:08.645949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '240aa81ababc'
down_revision = 'dfa8f3833177'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fighters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('nickname', sa.String(length=255), nullable=True),
    sa.Column('weight_class', sa.String(length=100), nullable=True),
    sa.Column('record', sa.String(length=100), nullable=True),
    sa.Column('knockouts', sa.String(length=100), nullable=True),
    sa.Column('submissions', sa.String(length=100), nullable=True),
    sa.Column('first_round_finishes', sa.String(length=100), nullable=True),
    sa.Column('takedown_accuracy', sa.String(length=100), nullable=True),
    sa.Column('striking_accuracy', sa.String(length=100), nullable=True),
    sa.Column('sig_str_landed_total', sa.String(length=100), nullable=True),
    sa.Column('sig_str_attempted_total', sa.String(length=100), nullable=True),
    sa.Column('takedowns_landed_total', sa.String(length=100), nullable=True),
    sa.Column('takedowns_attempted_total', sa.String(length=100), nullable=True),
    sa.Column('sig_strikes_per_min', sa.String(length=100), nullable=True),
    sa.Column('takedown_avg_per_min', sa.String(length=100), nullable=True),
    sa.Column('sig_str_def', sa.String(length=100), nullable=True),
    sa.Column('knockdown_avg', sa.String(length=100), nullable=True),
    sa.Column('sig_strikes_absorbed_per_min', sa.String(length=100), nullable=True),
    sa.Column('sub_avg_per_min', sa.String(length=100), nullable=True),
    sa.Column('takedown_def', sa.String(length=100), nullable=True),
    sa.Column('avg_fight_time', sa.String(length=100), nullable=True),
    sa.Column('sig_strikes_while_standing', sa.String(length=100), nullable=True),
    sa.Column('sig_strikes_while_clinched', sa.String(length=100), nullable=True),
    sa.Column('sig_strikes_while_grounded', sa.String(length=100), nullable=True),
    sa.Column('win_by_ko_tko', sa.String(length=100), nullable=True),
    sa.Column('win_by_decision', sa.String(length=100), nullable=True),
    sa.Column('win_by_submission', sa.String(length=100), nullable=True),
    sa.Column('image_url', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('fighter')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fighter',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('gym', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('SLpM', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('TDAcc', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('Age', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('Height', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('Reach', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('wins', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('losses', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('draws', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('ko_percentage', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('sub_percentage', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('dec_percentage', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('image_url', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('weight_class', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='fighter_pkey'),
    sa.UniqueConstraint('name', name='fighter_name_key')
    )
    op.drop_table('fighters')
    # ### end Alembic commands ###
