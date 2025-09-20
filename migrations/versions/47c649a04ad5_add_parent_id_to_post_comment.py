"""Add parent_id to post_comment

Revision ID: 47c649a04ad5
Revises: 143a0d8271b9
Create Date: 2025-09-19 23:52:07.261903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47c649a04ad5'
down_revision = '143a0d8271b9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands fixed to include constraint names ###
    with op.batch_alter_table('blog_comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_blog_comment_parent',  # constraint name
            'blog_comment',            # referred table
            ['parent_id'],             # local column
            ['id']                     # remote column
        )

    with op.batch_alter_table('post_comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_post_comment_parent',  # constraint name
            'post_comment',
            ['parent_id'],
            ['id']
        )


def downgrade():
    # ### drop constraints by name ###
    with op.batch_alter_table('post_comment', schema=None) as batch_op:
        batch_op.drop_constraint('fk_post_comment_parent', type_='foreignkey')
        batch_op.drop_column('parent_id')

    with op.batch_alter_table('blog_comment', schema=None) as batch_op:
        batch_op.drop_constraint('fk_blog_comment_parent', type_='foreignkey')
        batch_op.drop_column('parent_id')