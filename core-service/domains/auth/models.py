# domains/auth/models.py — User entity (no cross-domain ORM relationships)
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from common.base import Base


class User(Base):
    __tablename__ = "auth_users"

    # 1. Identity
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    phone_code: Mapped[str] = mapped_column(String(10), default="86", server_default="86")

    # 2. Security credentials
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 3. MFA
    mfa_secret: Mapped[str | None] = mapped_column(String(100))
    is_mfa_enabled: Mapped[bool] = mapped_column(default=False, server_default="false")

    # 4. Security version (core: supports force-invalidate tokens)
    version: Mapped[int] = mapped_column(default=1, server_default="1")

    # 5. Status & logical FKs
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    # Logical FK — no ORM relationship; identity domain owns Department
    dept_id: Mapped[int | None] = mapped_column(
        ForeignKey("auth_departments.id"), nullable=True
    )

    # NOTE: roles relationship removed for domain isolation.
    # Use IdentityService.get_user_roles_for_app() instead.

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, version={self.version})>"
