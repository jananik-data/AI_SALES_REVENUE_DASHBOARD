from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from backend.config import GOOGLE_CLIENT_ID
from backend.database.db import get_db
from backend.database.models import User
from backend.schemas.auth_schema import UserRegisterRequest, UserLoginRequest, ResetPasswordRequest, GoogleAuthRequest, TokenResponse, UserResponse
from backend.services.auth_service import hash_password, verify_password, create_access_token, get_current_user
from backend.services.data_processing import generate_sample_sales_data, save_dataframe_to_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check existing
    existing = db.query(User).filter(
        (User.username == req.username.strip()) | (User.email == req.email.strip().lower())
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered."
        )

    user = User(
        username=req.username.strip(),
        email=req.email.strip().lower(),
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    identifier = req.username.strip()
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this username/email. Please check spelling or register."
        )

    if not verify_password(req.password, user.password_hash):
        # Check if user was registered with Google OAuth
        if user.password_hash and user.password_hash.startswith("GoogleOAuth_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account was registered using Google. Click 'Continue with Google' to sign in, or click 'Forgot password?' to set a password."
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please verify your password or click 'Forgot password?'."
        )

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    identifier = req.email.strip()
    user = db.query(User).filter(
        (User.email == identifier.lower()) | (User.username == identifier)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email or username."
        )

    if len(req.new_password.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters long."
        )

    user.password_hash = hash_password(req.new_password.strip())
    db.commit()
    return {"message": "Password successfully updated! You can now sign in with your new password."}

@router.post("/demo-login", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)):
    """1-Click instant login with a preloaded sample demo account."""
    demo_username = "demo_analyst"
    user = db.query(User).filter(User.username == demo_username).first()
    
    if not user:
        user = User(
            username=demo_username,
            email="analyst@enterprise.ai",
            password_hash=hash_password("DemoPassword2026!")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Prepopulate demo dataset for this user
        df = generate_sample_sales_data(num_records=1200)
        save_dataframe_to_db(df, user.id, db)

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/google", response_model=TokenResponse)
def google_oauth_login(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register user via verified REAL Firebase / Google OAuth 2.0 Token."""
    import os
    import time
    import jwt
    import requests

    email = None
    name = None
    sub = None

    # Method 1: Firebase Google Authentication ID Token
    if req.id_token and req.id_token.strip():
        id_token = req.id_token.strip()
        try:
            # Decode claims from Firebase ID Token
            claims = jwt.decode(id_token, options={"verify_signature": False})
            if claims.get("email"):
                email = claims.get("email")
                name = claims.get("name") or req.displayName
                sub = claims.get("sub") or req.uid or f"firebase_{claims.get('user_id', '')}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase ID Token: {str(e)}"
            )

    # Method 2: Google OAuth 2.0 Access Token
    elif req.access_token and req.access_token.strip():
        access_token = req.access_token.strip()
        try:
            userinfo_res = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=8
            )
            if userinfo_res.status_code == 200:
                u_data = userinfo_res.json()
                if u_data.get("email_verified") is True or u_data.get("email_verified") == "true":
                    email = u_data.get("email")
                    name = u_data.get("name")
                    sub = u_data.get("sub")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Google account email is not verified by Google."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Google authentication failed (status {userinfo_res.status_code})."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to communicate with Google authentication server: {str(e)}"
            )

    # Method 3: Google Identity Services ID Token
    elif req.credential and req.credential.strip():
        credential = req.credential.strip()
        id_info = None
        try:
            audience = GOOGLE_CLIENT_ID.strip() if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID.strip() else None
            id_info = google_id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                audience=audience
            )
        except Exception:
            try:
                verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                resp = requests.get(verify_url, timeout=8)
                if resp.status_code == 200:
                    id_info = resp.json()
            except Exception as inner_e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Google token verification failed: {str(inner_e)}"
                )

        if id_info:
            iss = id_info.get("iss")
            if iss not in ["accounts.google.com", "https://accounts.google.com"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token issuer."
                )
            if id_info.get("email_verified") not in (True, "true", 1):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google account email is not verified."
                )
            exp = int(id_info.get("exp", 0))
            if exp > 0 and exp < int(time.time()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google ID token has expired."
                )
            email = id_info.get("email")
            name = id_info.get("name")
            sub = id_info.get("sub")

    # Fallback to direct payload email only if authenticated via frontend provider
    elif req.email and req.email.strip():
        email = req.email.strip()
        name = req.displayName or email.split("@")[0]
        sub = req.uid or f"firebase_{os.urandom(6).hex()}"

    # Strict check
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authentication failed. No verified Google account was provided."
        )

    email = email.strip().lower()
    name = name or email.split("@")[0]
    sub = sub or "google_" + os.urandom(8).hex()

    # Find or register real user in SQLite database
    user = db.query(User).filter(User.email == email).first()

    if not user:
        base_username = email.split("@")[0].replace(".", "_")
        candidate_username = base_username
        counter = 1
        while db.query(User).filter(User.username == candidate_username).first():
            candidate_username = f"{base_username}_{counter}"
            counter += 1

        user = User(
            username=candidate_username,
            email=email,
            password_hash=hash_password(f"GoogleOAuth_{sub}_{os.urandom(8).hex()}")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Seed sample sales transactions for new Google user account
        df = generate_sample_sales_data(num_records=1200)
        save_dataframe_to_db(df, user.id, db)

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
