"""
Sales crud
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud.base import CRUDBase
from bot.db.models import SalesDate


class CRUDSales(CRUDBase):
    """
    Implements SalesDate specific methods
    """

    async def is_a_sale_now(
            self,
            session: AsyncSession,
    ) -> bool:
        """
        Returns bool depending on whether sales are possible now or not
        """
        today = datetime.now()
        db_obj = await session.execute(
            select(self.model).where(
                (self.model.is_active) & (today >= self.model.sales_start) & (today <= self.model.sales_finish)
            )
        )
        return bool(db_obj.scalars().first())

    async def get_active_sales(
        self,
        session: AsyncSession,
    ) -> list[SalesDate]:
        db_objs = await session.execute(
            select(self.model).where(
                (self.model.is_active)
            )
        )
        return db_objs.scalars().all()


sales_crud = CRUDSales(SalesDate)
