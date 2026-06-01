from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dao import user_dao
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, ChangePasswordRequest, LoginResponse, UserInfo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def authenticate(db: AsyncSession, req: LoginRequest) -> LoginResponse:
    user = await user_dao.get_by_username(db, req.username)
    if not user or not verify_password(req.password, user.password_hash):
        raise ValueError("用户名或密码错误")
    if user.status == "disabled":
        raise ValueError("账号已被禁用")
    token = create_token(user.id)
    return LoginResponse(
        access_token=token,
        user=UserInfo(id=user.id, username=user.username, role=user.role, status=user.status),
    )


async def register(db: AsyncSession, req: RegisterRequest) -> UserInfo:
    existing = await user_dao.get_by_username(db, req.username)
    if existing:
        raise ValueError("用户名已存在")
    user = User(username=req.username, password_hash=hash_password(req.password), role="user", status="active")
    user = await user_dao.create(db, user)
    return UserInfo(id=user.id, username=user.username, role=user.role, status=user.status)


async def change_password(db: AsyncSession, user: User, req: ChangePasswordRequest) -> None:
    if not verify_password(req.old_password, user.password_hash):
        raise ValueError("原密码错误")
    await user_dao.update_user(db, user.id, password_hash=hash_password(req.new_password))


async def create_user(db: AsyncSession, username: str, password: str, role: str = "user") -> UserInfo:
    existing = await user_dao.get_by_username(db, username)
    if existing:
        raise ValueError("用户名已存在")
    user = User(username=username, password_hash=hash_password(password), role=role, status="active")
    user = await user_dao.create(db, user)
    return UserInfo(id=user.id, username=user.username, role=user.role, status=user.status)


async def reset_password(db: AsyncSession, user_id: int, new_password: str) -> None:
    await user_dao.update_user(db, user_id, password_hash=hash_password(new_password))


async def toggle_status(db: AsyncSession, user_id: int) -> str:
    user = await user_dao.get_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    new_status = "disabled" if user.status == "active" else "active"
    await user_dao.update_user(db, user_id, status=new_status)
    return new_status
