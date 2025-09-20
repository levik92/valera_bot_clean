from __future__ import annotations
from typing import Optional

from sqlalchemy import String, BigInteger, Integer, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import mapped_column, DeclarativeBase, Mapped, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    requests: Mapped[int] = mapped_column(Integer, default=30)

    referrals = relationship("Referral", back_populates="referrer", foreign_keys="[Referral.user_id]")

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"))  # Исправлен тип
    referral_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"))  # Добавлен тип и FK

    referrer = relationship("User", back_populates="referrals", foreign_keys=[user_id])
    referred_user = relationship("User", foreign_keys=[referral_id])