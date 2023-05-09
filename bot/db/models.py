"""
User model
"""
from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    Boolean,
    VARCHAR,
    DateTime,
    Integer,
    ForeignKey,
    BigInteger, select,
)
from sqlalchemy.orm import relationship, sessionmaker

from bot.db.base import CustomBaseModel, BaseModel, get_object


class User(
    CustomBaseModel,
):
    """
    User model
    """
    __tablename__ = "users"

    # telegram username
    username = Column(VARCHAR(32))

    is_active = Column(Boolean, default=False)

    subscription_date = Column(DateTime, name="sub_date")
    unsubscribe_date = Column(DateTime, name="unsub_date")

    payment_id = Column(Integer, ForeignKey('payments.id'))
    payment = relationship('Payment', uselist=False, back_populates="user")

    def is_need_to_kick(self):
        return self.is_active and self.unsubscribe_date is not None and self.unsubscribe_date < datetime.now()

    def __str__(self):
        return f"<User:{self.id} {self.username}>"


class Payment(BaseModel):
    """
    Payments table
    """
    __tablename__ = "payments"
    id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    payment_name = Column(VARCHAR(32), nullable=False, name="payment_period_name")
    humanize_name = Column(VARCHAR(32), name="humanize_name")

    payment_amount = Column(Integer, nullable=True, name="payment_amount", default=0)
    payment_currency = Column(VARCHAR(5), default="RUB", nullable=True)

    sub_period = Column(Integer, nullable=False, name="sub_period")
    user = relationship("User", uselist=False, back_populates="payment")


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
        user_id: int,
        sub_period: int,
        session: sessionmaker,
) -> User:
    async with session() as session_:
        async with session_.begin():
            user = await get_object(User, id_=user_id, session=session)
            payment = tuple(
                (await session_.execute(select(Payment).
                                        where(Payment.sub_period == sub_period))).scalars())[0]
            user.payment = payment
            user.subscription_date = datetime.utcnow()
            user.unsubscribe_date = datetime.utcnow() + timedelta(sub_period * 30)
            user.is_active = True
            session_.add(user)
            await session_.flush()
    return user
