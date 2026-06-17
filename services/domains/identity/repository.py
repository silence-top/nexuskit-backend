# domains/identity/repository.py — Permission data access
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Permission


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, menu_id: int) -> Permission | None:
        return await self.session.get(Permission, menu_id)

    async def get_children(self, menu_id: int) -> list[Permission]:
        result = await self.session.execute(
            select(Permission).where(Permission.parent_id == menu_id)
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> Permission:
        perm = Permission(**data)
        self.session.add(perm)
        await self.session.flush()
        return perm

    async def update(self, menu_id: int, data: dict) -> Permission | None:
        perm = await self.get_by_id(menu_id)
        if perm is None:
            return None
        for key, value in data.items():
            setattr(perm, key, value)
        await self.session.flush()
        return perm

    async def delete(self, menu_id: int) -> bool:
        await self.session.execute(delete(Permission).where(Permission.id == menu_id))
        return True
