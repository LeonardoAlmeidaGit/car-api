from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Numeric, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from car_api.models import Base


class Brand(Base):
    __tablename__ = 'brands'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
