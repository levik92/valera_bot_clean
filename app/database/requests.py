from typing import Optional
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Referral


async def add_user(
    session: AsyncSession, 
    tg_id: int,
    name: str,
    username: Optional[str] = None
):
    result = await session.scalar(
        select(User).filter(User.tg_id == tg_id)
    )
    if result:
        return result
    user = User(
        tg_id=tg_id,
        username=username,
        name=name
    )
    session.add(user)
    await session.commit()
    print(f"User {name} was added") 
    return user


async def get_user(
    session: AsyncSession,
    tg_id: int
) -> (User | None):
    return await session.scalar(
        select(User).filter(User.tg_id == tg_id)
    )
     

async def get_referral(
    session: AsyncSession,
    user_id: int,
    inviter_id: int
) -> (Referral | None):
    result = await session.scalar(
        select(Referral).filter(
            or_(
                Referral.user_id == user_id,
                Referral.referral_id == inviter_id,
                Referral.referral_id == user_id
            )
        )
    )
    return result


async def add_referral(
    session: AsyncSession,
    user_id: int,
    inviter_id: int
) -> None:
    referral = Referral(
        user_id=user_id,
        referral_id=inviter_id
    )
    session.add(referral)
    await session.commit()
    print(f"Referral {user_id} was added")


async def decrease_user_request(
    session: AsyncSession,
    user_id: int
):
    user = await session.scalar(
        select(User).filter(User.tg_id == user_id)
    )
    if not user:
        return
    user.requests -= 1
    await session.commit()
    return True


async def update_user_requests(
    session: AsyncSession,
    user_id: int,
    quantity: int
):
    user = await session.scalar(
        select(User).filter(User.tg_id == user_id)
    )
    if not user:
        return
    user.requests += quantity
    await session.commit()
    return True