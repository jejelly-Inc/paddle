
from sqlalchemy import (Boolean, Column, Integer,
                        String, text, Float, ForeignKey)
from sqlalchemy.sql.sqltypes import TIMESTAMP, DATE
from sqlalchemy.orm import relationship
import uuid


from database import Base


class Plan(Base):
    __tablename__ = "plans"
    # id = Column(Integer, , autoincrement=True,
    #             nullable=False, index=True)
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, unique=False, nullable=False)
    billing_type = Column(String, nullable=False)
    billing_period = Column(Integer, unique=False, nullable=False)
    trial_days = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    # price = relationship("Price", back_populates='plan')


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, autoincrement=True,
                nullable=False, index=True)
    currency = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    recurring = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    plan_id = Column(Integer, ForeignKey(
        'plans.id', ondelete="CASCADE"), primary_key=True, autoincrement='ignore_fk')
    plan = relationship("Plan")
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,
                     nullable=True)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    under_plan = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Subscribers(Base):
    __tablename__ = 'subscribers'
    id = Column(Integer, primary_key=True,
                nullable=False)
    plan_id = Column(Integer)
    user_id = Column(Integer, nullable=False)
    user_email = Column(String(100))
    marketing_consent = Column(Boolean(100))
    update_url = Column(String(200))
    cancel_url = Column(String(200))
    state = Column(String(100))
    signup_date = Column(TIMESTAMP(timezone=True),
                         nullable=False)
    currency = Column(String(20))

    next_bill_date = Column(TIMESTAMP(timezone=True),
                            nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    next_payment_amount = Column(Float, nullable=False)
    next_payment_date = Column(DATE(),
                               nullable=False)

    last_payment_amount = Column(Float, nullable=False)
    last_payment_date = Column(DATE(),
                               nullable=False)
    payment_method = Column(String, nullable=False)
    card_type = Column(String, nullable=False)
    last_four_digits = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)


class Subscription(Base):
    __tablename__ = 'subscriptions'
    # Sibcription id is same as id here
    id = Column(Integer, primary_key=True,
                nullable=False)
    checkout_id = Column(Integer, nullable=False)
    currency = Column(String(20))
    email = Column(String(100))
    event_time = Column(TIMESTAMP(timezone=True),
                        nullable=False)
    marketing_consent = Column(Boolean(100))
    next_bill_date = Column(TIMESTAMP(timezone=True),
                            nullable=False)
    passthrough = Column(String)
    quantity = Column(Integer)
    source = Column(String(200))
    user_id = Column(Integer, nullable=False)
    status = Column(String(100))
    plan_id = Column(Integer, nullable=False)
    unit_price = Column(Float)
    update_url = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Usage_Information(Base):
    __tablename__ = 'usage_information'
    id = Column(Integer, primary_key=True, autoincrement=True,
                nullable=False, index=True)
    model_user_id = Column(Integer, ForeignKey(
        'users.id', ondelete="CASCADE"), primary_key=True, autoincrement='ignore_fk')
    initial_data = Column(Integer)
    plan_id = Column(Integer, nullable=False)
    subscription_id = Column(Integer, nullable=False)
    current_data = Column(Integer)
    extra_charges = Column(Float)
    user_id = Column(Integer,
                     nullable=False)
