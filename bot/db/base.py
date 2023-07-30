"""
BaseModel sql alchemy
"""
import datetime

from sqlalchemy import Column, BigInteger, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class CustomBaseModel(BaseModel):
    __abstract__ = True

    id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.now, name="created")
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, name="updated")

    is_deleted = Column(Boolean, default=False)
