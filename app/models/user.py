from pydantic import BaseModel, Field


class UserRegistrationRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str
    age: int | None = Field(default=None, ge=0, le=150)
    assistant_name: str = "WilliamOS"


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: str | None = None
    email: str
    full_name: str
    age: int | None = None
    assistant_name: str = "WilliamOS"
    created_at: str | None = None
    updated_at: str | None = None


class AuthenticatedUser(UserProfile):
    access_token: str | None = None
    refresh_token: str | None = None
