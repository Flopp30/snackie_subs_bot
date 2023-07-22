from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.base import BaseModel
from bot.db.models import User


class CRUDBase:
    """
    Basic CRUD operaions to work with db.
    """

    def __init__(self, model):
        self.model = model

    async def get_by_id(
            self,
            obj_id: int,
            session: AsyncSession,
    ) -> BaseModel:
        """
        Returns db_object by it's id value.
        """
        db_obj = await session.execute(
            select(self.model).where(
                self.model.id == obj_id
            )
        )
        return db_obj.scalars().first()

    async def get_by_attribute(
            self,
            attr_name: str,
            attr_value: str | int | bool,
            session: AsyncSession,
            is_deleted: Optional[bool] = None,
    ) -> BaseModel:
        """
        Returns db_object by any attr value.
        """
        attr = getattr(self.model, attr_name)

        if is_deleted is not None and self.model == User:
            db_obj = await session.execute(
                select(self.model).where(
                    attr == attr_value, self.model.is_deleted == is_deleted
                )
            )
            return db_obj.scalars().first()

        db_obj = await session.execute(
            select(self.model).where(attr == attr_value)
        )
        return db_obj.scalars().first()

    async def get_multi(
            self,
            session: AsyncSession
    ) -> Sequence[BaseModel]:
        """
        Returns list of db_objects
        """
        db_objs = await session.execute(select(self.model).order_by(self.model.id))
        return db_objs.scalars().all()

    async def create(
            self,
            obj_in_data: dict[str: str | int | bool],
            session: AsyncSession,
    ) -> BaseModel:
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
            self,
            db_obj: BaseModel,
            obj_in_data: dict[str: str | int | bool],
            session: AsyncSession,
    ) -> BaseModel:
        """
        Updates db_object and returns refreshed one.
        """
        for field, value in obj_in_data.items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(
            self,
            db_obj: BaseModel,
            session: AsyncSession,
    ) -> BaseModel:
        """
        Sets is_deleted status to deleted db_objects.
        """
        setattr(db_obj, "is_deleted", True)
        session.add(db_obj)
        await session.commit()
        return db_obj
