import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.core.security import (
    CurrentUser,
    create_access_token,
    get_current_user,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: CurrentUser


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    username_matches = secrets.compare_digest(
        payload.username,
        settings.admin_username,
    )

    password_matches = secrets.compare_digest(
        payload.password,
        settings.admin_password,
    )

    if not (username_matches and password_matches):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = CurrentUser(
        username=settings.admin_username,
        role="administrator",
    )

    return LoginResponse(
        access_token=create_access_token(
            username=user.username,
            role=user.role,
        ),
        token_type="bearer",
        user=user,
    )


@router.get("/me", response_model=CurrentUser)
def get_me(
        current_user: CurrentUser = Depends(get_current_user),
):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    return None