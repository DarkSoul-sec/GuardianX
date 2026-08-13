from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    SECURITY_ENGINEER = "SECURITY_ENGINEER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"
    USER = "USER"
