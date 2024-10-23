from __future__ import annotations
from datetime import date, datetime
from typing import List, Any
from sqlalchemy import ForeignKey, String, Identity, Date, BigInteger
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy.dialects.postgresql import JSONB


class Base(AsyncAttrs, DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB}