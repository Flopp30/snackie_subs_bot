"""
User model
"""
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List

from sqlalchemy import (
    Column,
    Boolean,
    VARCHAR,
    DateTime,
    Integer,
    ForeignKey,
    BigInteger,
    select,
    Float,
)
from sqlalchemy.orm import relationship, sessionmaker, Mapped

from bot.db.base import CustomBaseModel, BaseModel, get_object


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

    def is_subscribe_ended(self):
        return self.is_active and self.unsubscribe_date is not None and self.unsubscribe_date <= datetime.now()

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


async def create_user(
        user_args: dict,
        session: sessionmaker,
) -> User:
    """
    Create user
    :param user_args:
    :param session:
    :return: User
    """

    async with session() as session_:
        async with session_.begin():
            user = User(**user_args)
            session_.add(user)
            await session_.flush()
        return user


async def set_subscribe_after_payment(
        verified_payment_id: uuid,
        session: sessionmaker,
        first_time: bool,
        user_id: int = None,
        sub_id: int = None,
        user: User = None,
        subscription: Subscription = None,
) -> User:
    async with session() as session_:
        async with session_.begin():

            if user_id:
                user = await get_object(User, id_=user_id, session=session)
            if sub_id:
                subscription = await get_object(Subscription, id_=sub_id, session=session)

            if first_time:
                user.first_sub_date = datetime.now()

            user.unsubscribe_date = datetime.now() + relativedelta(months=subscription.sub_period)
            user.is_active = True
            user.subscription = subscription
            user.is_accepted_for_auto_payment = True
            user.verified_payment_id = verified_payment_id
            session_.add(user)
            await session_.flush()
    return user


async def unsubscribe_user(
        session,
        user: User,
):
    async with session() as session:
        async with session.begin():
            user.unsubscribe_date = None
            user.is_active = False
            user.subscription_id = None
            user.subscription = None
            user.is_accepted_for_auto_payment = False
            user.verified_payment_id = None
            session.add(user)
            await session.flush()


async def create_payment(
        user_id: int,
        status: str,
        payment_amount: float,
        verified_payment_id: str,
        session: sessionmaker,
) -> Payment:
    async with session() as session_:
        async with session_.begin():
            user = tuple((await session_.execute(select(User).where(User.id == user_id))).scalars())[0]
            payment = Payment(
                status=status,
                payment_amount=payment_amount,
                date=datetime.now(),
                user=user,
            )
            user.verified_payment_id = verified_payment_id
            session_.add(user)
            session_.add(payment)
            await session_.flush()
        return payment
