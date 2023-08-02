from datetime import datetime
from typing import Sequence

from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Payment, User, BaseModel
from bot.db.crud.base import CRUDBase
from bot.db.crud.user import user_crud


class CRUDPayment(CRUDBase):
    """
    Implements Payment specific methods
    """

    async def create_payment(
            self,
            status: str,
            payment_amount: float,
            session: AsyncSession,
            user_id: int = None,
            user: User = None,
    ) -> BaseModel:
        """
        Creates a payment, sets the verified payment id to the user, if it was transferred
        """
        if user_id:
            user = await user_crud.get_by_id(user_pk=user_id, session=session)
        payment = self.model(
            status=status,
            payment_amount=payment_amount,
            date=datetime.now(),
            user=user,
        )

        session.add(payment)
        session.add(user)
        await session.commit()
        await session.refresh(payment)
        await session.refresh(user)
        return payment

    async def get_this_month_multi(
            self,
            session: AsyncSession,
    ) -> Sequence[BaseModel]:
        """
        Returns a list of payments for this month
        """
        date_now = datetime.now()
        current_month = date_now.month
        db_obj = await session.execute(
            select(self.model).where(
                (extract('month', self.model.date) == current_month)
            )
        )
        return db_obj.scalars().all()


payment_crud = CRUDPayment(Payment)
