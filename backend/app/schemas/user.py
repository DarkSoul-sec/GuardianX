from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.roles import UserRole


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique username",
    )

    email: EmailStr

    password: str = Field(
        min_length=12,
        description="Strong password",
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    role: UserRole
    is_active: bool
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    email: EmailStr | None = None


class UserPasswordChange(BaseModel):
    current_password: str

    new_password: str = Field(
        min_length=12,
        description="Strong password",
    )


class RoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
