# domains/auth/repository.py — User data access
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def list_users(
        self,
        keyword: str | None = None,
        is_active: bool | None = None,
        dept_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """Paginated user list with optional filters."""
        stmt = select(User)
        if keyword:
            stmt = stmt.where(
                or_(User.username.ilike(f"%{keyword}%"), User.email.ilike(f"%{keyword}%"))
            )
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if dept_id is not None:
            stmt = stmt.where(User.dept_id == dept_id)

        count_result = await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total = count_result.scalar_one()

        stmt = stmt.order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, username: str, email: str, hashed_password: str, **kwargs) -> User:
        kwargs.setdefault("is_active", True)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            version=1,
            **kwargs,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User, **fields) -> User:
        for k, v in fields.items():
            setattr(user, k, v)
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
