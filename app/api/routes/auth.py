from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.services.auth_core import context_to_response, sign_in, sign_up
from app.services.profile_service import get_assistant_name

router = APIRouter()


class SignUpRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1)
    household_name: str = Field(min_length=1)


class SignInRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: str
    email: str
    household_id: str
    display_name: str | None = None
    assistant_name: str | None = None
    access_token: str
    refresh_token: str


class MeResponse(BaseModel):
    user_id: str
    email: str
    household_id: str
    display_name: str | None = None
    assistant_name: str | None = None


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignUpRequest):
    try:
        context = sign_up(
            request.email,
            request.password,
            request.display_name,
            request.household_name,
        )
    except RuntimeError as exc:
        message = str(exc)
        status_code = status.HTTP_202_ACCEPTED if "Bekreft e-posten" in message else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc
    return context_to_response(context)


@router.post("/login", response_model=AuthResponse)
def login(request: SignInRequest):
    try:
        context = sign_in(request.email, request.password)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return context_to_response(context)


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser):
    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        household_id=user.household_id,
        display_name=user.display_name,
        assistant_name=get_assistant_name(),
    )
