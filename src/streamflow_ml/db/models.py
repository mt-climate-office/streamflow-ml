from __future__ import annotations
from sqlalchemy import String, ForeignKey, Date, Float, Column
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geometry


class Base(AsyncAttrs, DeclarativeBase): ...


class Locations(Base):
    __tablename__ = "locations"
    __table_args__ = {"schema": "flow", "extend_existing": True}

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    group: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))

    # https://github.com/rhoboro/async-fastapi-sqlalchemy/blob/main/app/api/notebooks/views.py
    @classmethod
    async def create(cls, session: AsyncSession):
        pass


class Data(Base):
    __tablename__ = "data"
    __table_args__ = {"schema": "flow", "extend_existing": True}

    location: Mapped[str] = mapped_column(
        ForeignKey("flow.locations.id"), primary_key=True, index=True
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True, index=True)
    version: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    value: Mapped[float] = mapped_column(Float)
