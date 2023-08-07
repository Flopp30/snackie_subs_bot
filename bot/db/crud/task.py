"""
Task crud
"""
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud.base import CRUDBase
from bot.db.models import Tasks


class CRUDTask(CRUDBase):
    """
    Implements User specific methods
    """

    async def get_active_payment_process_tasks_by_user_id(
            self,
            user_pk: int,
            session: AsyncSession,
    ) -> Sequence[Tasks]:
        """
        Returns tasks by user id value.
        """
        db_obj = await session.execute(
            select(self.model).where(
                self.model.user_id == user_pk,
                self.model.status == 'active',
                self.model.type == 'payment_process'
            )
        )
        return db_obj.scalars().all()

    async def mark_as_done_payment_process_tasks_by_user_id(self, user_id, session: AsyncSession):
        """
            Mark as done tasks by user id value
        """
        tasks = await self.get_active_payment_process_tasks_by_user_id(user_id, session)
        for task in tasks:
            task.status = 'done'
            session.add(task)
        await session.commit()


task_crud = CRUDTask(Tasks)
