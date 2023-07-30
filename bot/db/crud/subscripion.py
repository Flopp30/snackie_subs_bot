from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import BaseModel
from bot.db import Subscription
from bot.db.crud.base import CRUDBase


class CRUDSub(CRUDBase):
    """
    Implements Subscription specific methods
    """
    async def get_multi(
            self,
            session: AsyncSession,
            with_trials: bool = True,
    ) -> Sequence[BaseModel]:
        """
        Returns list of db_objects
        """
        if with_trials:
            db_objs = await session.execute(select(self.model).order_by(self.model.id))
        else:
            db_objs = await session.execute(select(self.model).where(~self.model.is_trial).order_by(self.model.id))
        return db_objs.scalars().all()


sub_crud = CRUDSub(Subscription)
