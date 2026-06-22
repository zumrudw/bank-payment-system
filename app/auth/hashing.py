from passlib.context import CryptContext

# bcrypt is a battle-tested, slow-by-design hashing algorithm
# "slow by design" makes brute-force password guessing impractical
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Turns a plain text password into an irreversible hash."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if a plain password matches a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)