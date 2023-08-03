"""
User model
"""
from datetime import datetime
from typing import List

from sqlalchemy import (
    Column,
    Boolean,
    VARCHAR,
    DateTime,
    Integer,
    ForeignKey,
    BigInteger,
    Float,
)
from sqlalchemy.orm import relationship, Mapped

from bot.db.base import CustomBaseModel, BaseModel


class Subscription(BaseModel):
    """
    Subscriptions table
    """
    __tablename__ = "subscriptions"

    id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    payment_name = Column(VARCHAR(32), nullable=False)
    humanize_name = Column(VARCHAR(32), nullable=False)

    payment_amount = Column(Integer, nullable=False, default=0)
    payment_currency = Column(VARCHAR(5), default="RUB", nullable=False)

    sub_period = Column(Integer, nullable=False)
    sub_period_type = Column(VARCHAR(32), default='month')
    is_trial = Column(Boolean, default=False)

    def __str__(self):
        return f"{self.id}:{self.payment_name}:{self.payment_currency}"

    def to_dict(self):
        return {
            "id": self.id,
            "payment_name": self.payment_name,
            "humanize_name": self.humanize_name,
            "payment_amount": self.payment_amount,
            "payment_currency": self.payment_currency,
            "sub_period": self.sub_period,
            "sub_period_type": self.sub_period_type,
            "is_trial": self.is_trial,
        }


class User(CustomBaseModel):
    """
    User model
    """
    __tablename__ = "users"

    # telegram username
    username = Column(VARCHAR(32))

    is_active = Column(Boolean, default=False)
    is_accepted_for_auto_payment = Column(Boolean, default=False)
    first_sub_date = Column(DateTime, name="sub_date")
    unsubscribe_date = Column(DateTime, name="unsub_date")
    verified_payment_id = Column(VARCHAR(128))

    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    subscription = relationship("Subscription", uselist=False)
    payments: Mapped[List["Payment"]] = relationship(back_populates="user")
    tasks: Mapped[List["Tasks"]] = relationship(back_populates="user")

    def is_subscribe_ended(self):
        return self.is_active and self.unsubscribe_date <= datetime.now()

    def __str__(self):
        return f"<User:{self.id} {self.username}>"


class Payment(BaseModel):
    """
    Payments table
    """
    __tablename__ = "payments"
    id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    status = Column(VARCHAR(32), nullable=False)

    payment_amount = Column(Float, nullable=False, default=0)
    date = Column(DateTime, nullable=False, name="payment_date")

    user_id: Mapped[int] = Column(BigInteger, ForeignKey('users.id'))
    user: Mapped["User"] = relationship(back_populates="payments")

    def __str__(self):
        return f"Payment:{self.id}:{self.date}:{self.payment_amount}"


class SalesDate(BaseModel):
    """
    Sales date models
    """
    __tablename__ = "sales_dates"
    id = Column(BigInteger, unique=True, nullable=False, primary_key=True)

    sales_start = Column(DateTime, default=datetime.now())
    sales_finish = Column(DateTime, default=datetime.now())

    is_active = Column(Boolean, default=True)


class Tasks(CustomBaseModel):
    __tablename__ = "tasks"
    type = Column(VARCHAR(128))
    status = Column(VARCHAR(128))
    message_id = Column(BigInteger)
    job_id = Column(VARCHAR(128))
    user_id: Mapped[int] = Column(BigInteger, ForeignKey('users.id'))
    user: Mapped["User"] = relationship(back_populates="tasks")
