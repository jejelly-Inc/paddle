"""updated one

Revision ID: 66765f37b764
Revises: 
Create Date: 2022-05-24 23:03:05.157460

"""
from sqlalchemy.sql import insert
from paddle import PaddleClient
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66765f37b764'
down_revision = None
branch_labels = None
depends_on = None

paddle_client = PaddleClient(
    vendor_id=147688, api_key='9b6bb011a039da46a0be9f4fbf828da9a48579a4f681ab0e91')


def upgrade():
    plans = op.create_table('plans',
                            sa.Column('id', sa.Integer(), nullable=False),
                            sa.Column('name', sa.String(), nullable=False),
                            sa.Column('billing_type', sa.String(),
                                      nullable=False),
                            sa.Column('billing_period',
                                      sa.Integer(), nullable=False),
                            sa.Column('trial_days', sa.Integer(),
                                      nullable=False),
                            sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                                      server_default=sa.text('now()'), nullable=False),
                            sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                                      server_default=sa.text('now()'), nullable=False),
                            sa.PrimaryKeyConstraint('id')
                            )

    prices = op.create_table('prices',
                             sa.Column('id', sa.Integer(),
                                       autoincrement=True, nullable=False),
                             #  sa.PrimaryKeyConstraint('id'),
                             sa.Column('currency', sa.String(),
                                       nullable=False),
                             sa.Column('quantity', sa.Float(), nullable=False),
                             sa.Column('recurring', sa.Boolean(),
                                       nullable=False),
                             sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                                       server_default=sa.text('now()'), nullable=False),
                             sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                                       server_default=sa.text('now()'), nullable=False),
                             sa.Column('plan_id', sa.Integer(),
                                       nullable=False),
                             sa.ForeignKeyConstraint(
                                 ['plan_id'], ['plans.id'], ondelete='CASCADE'),
                             sa.PrimaryKeyConstraint('id', 'plan_id')
                             )

    # op.add_column('prices', sa.Column('plan_id', sa.Integer(), nullable=False))
    # op.create_foreign_key('fk_plans_prices', source_table='prices', referent_table='plans',
    #                       local_cols=['plan_id'], remote_cols=['id'], ondelete='CASCADE')
    paddle_list = paddle_client.list_plans()

    # def sync_from_paddle_data(data):
    #     id = data["id"]
    #     initial_price = data.pop("initial_price", {})
    #     recurring_price = data.pop("recurring_price", {})
    #     op.execute(insert(plans).values(data))
    #     price_list = []
    #     for currency, quantity in initial_price.items():
    #         price = {}
    #         price['plan_id'] = id
    #         price['currency'] = currency
    #         price['quantity'] = quantity
    #         price['recurring'] = False
    #         prices.append(price)
    #     for currency, quantity in recurring_price.items():
    #         price = {}
    #         price['plan_id'] = id
    #         price['currency'] = currency
    #         price['quantity'] = quantity
    #         price['recurring'] = True
    #         prices.append(price)
    #     op.bulk_insert(prices, price_list)

    for plan in paddle_list:
        data = plan
        id = data['id']
        initial_price = data.pop("initial_price", {})
        recurring_price = data.pop("recurring_price", {})
        op.execute(insert(plans).values(data))

        for currency, quantity in initial_price.items():
            price = {}
            price['plan_id'] = id
            price['currency'] = currency
            price['quantity'] = quantity
            price['recurring'] = False
            op.execute(insert(prices).values(price))
        for currency, quantity in recurring_price.items():
            price['plan_id'] = id
            price['currency'] = currency
            price['quantity'] = quantity
            price['recurring'] = True
            op.execute(insert(prices).values(price))
    pass


def downgrade():
    pass
