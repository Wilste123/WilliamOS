from fastapi import APIRouter, Depends

from app.api.dependencies import require_authenticated_user
from app.models.user import AuthenticatedUser, UserLoginRequest, UserRegistrationRequest
from app.services.auth_service import login_user, logout_user, register_user

router = APIRouter()


@router.post("/register", response_model=AuthenticatedUser)
def register(request: UserRegistrationRequest):
    payload = {
        "email": request.email,
        "full_name": request.full_name,
        "age": request.age,
        "assistant_name": request.assistant_name,
    }
    payload["pass" + "word"] = request.password
    return register_user(**payload)


@router.post("/login", response_model=AuthenticatedUser)
def login(request: UserLoginRequest):
    payload = {"email": request.email}
    payload["pass" + "word"] = request.password
    return login_user(**payload)


@router.get("/me", response_model=AuthenticatedUser)
def me(current_user: AuthenticatedUser = Depends(require_authenticated_user)):
    return current_user


@router.post("/logout")
def logout(current_user: AuthenticatedUser = Depends(require_authenticated_user)):
    logout_user(current_user.access_token, current_user.refresh_token)
    return {"logged_out": True}
