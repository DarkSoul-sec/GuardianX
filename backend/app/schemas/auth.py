from pydantic import BaseModel, EmailStr, Field


class AdminSetupRequest(BaseModel):
    """Credentials for the first-run local administrator."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique administrator username",
    )

    password: str = Field(
        min_length=12,
        description="Strong password",
    )


class SetupStatusResponse(BaseModel):
    initialized: bool
    auth_mode: str


class EmailVerificationRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    token: str

    new_password: str = Field(
        min_length=12,
        description="Strong password",
    )


class MessageResponse(BaseModel):
    message: str