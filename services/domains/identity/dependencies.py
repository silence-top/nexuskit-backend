# domains/identity/dependencies.py — Identity DI wiring
from typing import Annotated

from fastapi import Depends

from core.db import DbDep, RedisDep
from domains.identity.service import IdentityService


def get_identity_service(db: DbDep, redis: RedisDep) -> IdentityService:
    return IdentityService(db, redis)


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]
