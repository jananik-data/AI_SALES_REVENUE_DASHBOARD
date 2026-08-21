from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserLoginRequest(BaseModel):
    username: str # Accepts username or email
    password: str

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str

class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    credential: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None
    displayName: Optional[str] = None
    uid: Optional[str] = None
    photoURL: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
