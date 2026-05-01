from pwdlib import PasswordHash

# create hasher (Argon2 is default and recommended)
pwd_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_hasher.verify(password, hashed)
