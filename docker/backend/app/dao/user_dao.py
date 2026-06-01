from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from typing import Optional, List


async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_list(db: AsyncSession, page: int = 1, size: int = 20, keyword: str = "", role: str = "") -> tuple[List[User], int]:
    query = select(User)
    count_query = select(User)

    if keyword:
        query = query.where(User.username.contains(keyword))
        count_query = count_query.where(User.username.contains(keyword))
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    from sqlalchemy import func
    total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = total_result.scalar()

    query = query.order_by(User.id).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def create(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: int, **kwargs) -> None:
    await db.execute(update(User).where(User.id == user_id).values(**kwargs))


async def delete(db: AsyncSession, user_id: int) -> None:
    user = await get_by_id(db, user_id)
    if user:
        await db.delete(user)
