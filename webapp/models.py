from pydantic import BaseModel


# Security
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


# Admin
class GameInstruction(BaseModel):
    instruction: str


class Permission(BaseModel):
    player: str
    level: int
