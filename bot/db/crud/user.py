import uuid
from datetime import datetime
from typing import Sequence

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from bot.db import User, Subscription, BaseModel
from bot.db.crud.base import CRUDBase
from bot.db.crud.subscripion import sub_crud


class CRUDUser(CRUDBase):
    """
    Implements User specific methods
    """

    async def get_by_id(
            self,
            user_pk: int,
            session: AsyncSession,
    ) -> User:
        """
        Returns user's object by it's id value.
        """
        db_obj = await session.execute(
            select(self.model).where(
                self.model.id == user_pk
            ).options(selectinload(self.model.subscription))
        )
        return db_obj.scalars().first()

    async def set_subscribe(
            self,
            session: AsyncSession,
            user_id: int = None,
            sub_id: int = None,
            user: User = None,
            subscription: Subscription = None
    ) -> User:
        """
        Installs a subscription to the user. The subscription end date is also set
        """
        if user_id and user is None:
            user = await self.get_by_id(user_pk=user_id, session=session)
        if sub_id and subscription is None:
            subscription = await sub_crud.get_by_id(obj_id=sub_id, session=session)

        if not user.first_sub_date:
            user.first_sub_date = datetime.now()

        if subscription.sub_period_type == 'month':
            user.unsubscribe_date = datetime.now() + relativedelta(months=subscription.sub_period)
        elif subscription.sub_period_type == 'day':
            user.unsubscribe_date = datetime.now() + relativedelta(days=subscription.sub_period)

        user.is_active = True
        user.subscription = subscription
        user.is_accepted_for_auto_payment = not subscription.is_trial
        session.add(user)
        await session.commit()
        return user

    async def unsubscribe(self, db_obj: User, session: AsyncSession) -> User:
        """
        Unsubscribes the user
        """
        unsubscribe_params = {
            "unsubscribe_date": None,
            "is_active": False,
            "subscription_id": None,
            "subscription": None,
            "is_accepted_for_auto_payment": False,
            "verified_payment_id": None,
        }

        return await self.update(db_obj, obj_in_data=unsubscribe_params, session=session)

    async def get_expired_sub_users(
            self,
            session: AsyncSession
    ) -> Sequence[User]:
        """
        Returns a list of users with an expired subscription
        """
        db_obj = await session.execute(
            select(self.model).where(
                (self.model.is_active) &
                (self.model.unsubscribe_date <= datetime.now().date())
            ).options(selectinload(self.model.subscription))
        )
        return db_obj.scalars().all()

    async def get_expired_sub_this_month_users(
            self,
            session: AsyncSession
    ) -> Sequence[User]:
        """
        Returns a list of users with a subscription expiring this month
        """
        current_month = datetime.now().month
        db_obj = await session.execute(
            select(self.model).where(
                (self.model.is_active) &
                (extract('month', self.model.unsubscribe_date) == current_month)
            ).options(selectinload(self.model.subscription))
        )
        return db_obj.scalars().all()

    async def get_multi(
            self,
            session: AsyncSession,
    ) -> Sequence[BaseModel]:
        """
        Returns list of users
        """
        db_objs = await session.execute(
            select(self.model)
            .options(
                joinedload(self.model.payments),
                selectinload(self.model.subscription)
            )
            .order_by(self.model.id))
        return db_objs.unique().scalars().all()


user_crud = CRUDUser(User)
