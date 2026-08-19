from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, use_user_context
from app.services.auth_core import context_to_response, sign_in, sign_up
from app.services.onboarding_service import complete_onboarding, get_onboarding_state, skip_onboarding
from app.services.profile_service import get_user_profile, update_assistant_name, update_user_profile

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    assistant_name: str | None = Field(default=None, min_length=1)
    display_name: str | None = Field(default=None, min_length=1)
    preferences: dict | None = None


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
    preferences: dict | None = None


class OnboardingRequest(BaseModel):
    assistant_name: str | None = Field(default=None, min_length=1)
    primary_use: str | None = None
    assets_mentioned: list[str] | None = None
    focus_now: str | None = Field(default=None, max_length=500)


class OnboardingResponse(BaseModel):
    onboarding_completed: bool
    assistant_name: str | None = None
    primary_use: str | None = None
    assets_mentioned: list[str] = Field(default_factory=list)
    focus_now: str | None = None


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
    use_user_context(user)
    profile = get_user_profile()
    return MeResponse(
        user_id=profile["user_id"],
        email=profile["email"],
        household_id=profile["household_id"],
        display_name=profile.get("display_name"),
        assistant_name=profile.get("assistant_name"),
        preferences=profile.get("preferences"),
    )


@router.patch("/profile")
def update_profile(request: ProfileUpdateRequest, user: CurrentUser):
    use_user_context(user)
    if request.assistant_name is not None and request.display_name is None and request.preferences is None:
        saved = update_assistant_name(request.assistant_name)
        return {"assistant_name": saved}

    profile = update_user_profile(
        display_name=request.display_name,
        assistant_name=request.assistant_name,
        preferences=request.preferences,
    )
    return profile


@router.get("/onboarding", response_model=OnboardingResponse)
def get_onboarding(user: CurrentUser):
    use_user_context(user)
    return OnboardingResponse(**get_onboarding_state())


@router.post("/onboarding", response_model=OnboardingResponse)
def post_onboarding(request: OnboardingRequest, user: CurrentUser):
    use_user_context(user)
    try:
        state = complete_onboarding(
            assistant_name=request.assistant_name,
            primary_use=request.primary_use,
            assets_mentioned=request.assets_mentioned,
            focus_now=request.focus_now,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return OnboardingResponse(**state)


@router.post("/onboarding/skip", response_model=OnboardingResponse)
def skip_onboarding_route(user: CurrentUser):
    use_user_context(user)
    return OnboardingResponse(**skip_onboarding())
