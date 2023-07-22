import uuid
from datetime import datetime
from typing import Sequence

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db import User, Subscription
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
        Returns db_object by it's id value.
        """
        db_obj = await session.execute(
            select(self.model).where(
                self.model.id == user_pk
            ).options(selectinload(self.model.subscription))
        )
        return db_obj.scalars().first()

    async def get_expired_sub_user(
            self,
            session: AsyncSession
    ) -> Sequence[User]:
        db_obj = await session.execute(
            select(self.model).where(
                    (self.model.is_active) &
                    (self.model.unsubscribe_date <= datetime.now().date())
            ).options(selectinload(self.model.subscription))
        )
        return db_obj.scalars().all()

    async def set_subscribe(
            self,
            session: AsyncSession,
            first_time: bool,
            user_id: int = None,
            sub_id: int = None,
            user: User = None,
            subscription: Subscription = None
    ) -> User:
        if user_id and user is None:
            user = await self.get_by_id(user_pk=user_id, session=session)
        if sub_id and subscription is None:
            subscription = await sub_crud.get_by_id(obj_id=sub_id, session=session)

        if first_time:
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
        unsubscribe_params = {
            "unsubscribe_date": None,
            "is_active": False,
            "subscription_id": None,
            "subscription": None,
            "is_accepted_for_auto_payment": False,
            "verified_payment_id": None,
        }

        return self.update(db_obj, obj_in_data=unsubscribe_params, session=session)


user_crud = CRUDUser(User)
