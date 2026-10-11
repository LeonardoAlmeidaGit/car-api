from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped,mapped_column

from models.base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    created_at = Mapped[datetime] = mapped_column(server_default=func.now())
