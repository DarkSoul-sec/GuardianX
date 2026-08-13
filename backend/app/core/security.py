from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password.
    """
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its hash.
    """
    return password_hash.verify(
        password,
        hashed_password,
    )
