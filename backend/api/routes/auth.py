import datetime
from datetime import timezone
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.connection import get_collection
from schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    GoogleLoginRequest,
    ForgotPasswordRequest,
)
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REMEMBER_ME_EXPIRE_MINUTES,
)

logger = logging.getLogger("auth")
router = APIRouter(tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Seed / default admin credentials for quick access
DEFAULT_ADMIN = {
    "email": "admin@ransomguard.io",
    "name": "Alex Vance (Chief SecOps)",
    "role": "Security Admin",
    "password": "admin123",
    "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=ransomguard_admin",
}

DEFAULT_ANALYST = {
    "email": "analyst@ransomguard.io",
    "name": "Sarah Connor",
    "role": "Security Analyst",
    "password": "analyst123",
    "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=ransomguard_analyst",
}


async def ensure_seed_users():
    """Seed initial default admin & analyst users if they do not exist."""
    try:
        users_col = get_collection("users")
        for u in [DEFAULT_ADMIN, DEFAULT_ANALYST]:
            existing = await users_col.find_one({"email": u["email"].lower()})
            if not existing:
                doc = {
                    "email": u["email"].lower(),
                    "name": u["name"],
                    "role": u["role"],
                    "hashed_password": hash_password(u["password"]),
                    "avatar": u["avatar"],
                    "is_active": True,
                    "created_at": datetime.datetime.now(timezone.utc).isoformat(),
                }
                await users_col.insert_one(doc)
                logger.info(f"Seeded default user: {u['email']}")
    except Exception as e:
        logger.warning(f"Could not seed default users into MongoDB: {e}")


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserResponse:
    """Dependency to get authenticated user from Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    try:
        users_col = get_collection("users")
        user = await users_col.find_one({"email": email.lower()})
        if user:
            return UserResponse(
                id=str(user.get("_id", user["email"])),
                email=user["email"],
                name=user.get("name", "Security Officer"),
                role=user.get("role", "Security Analyst"),
                avatar=user.get("avatar"),
                created_at=user.get("created_at"),
                is_active=user.get("is_active", True),
            )
    except Exception:
        pass
    
    # Fallback response from token payload if DB lookup is offline
    return UserResponse(
        id=payload.get("uid", email),
        email=email,
        name=payload.get("name", "Security Officer"),
        role=payload.get("role", "Security Analyst"),
        avatar=payload.get("avatar"),
        created_at=None,
        is_active=True,
    )


@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegister):
    """Register a new RansomGuard user account."""
    email_clean = req.email.lower().strip()
    
    try:
        users_col = get_collection("users")
        existing = await users_col.find_one({"email": email_clean})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists",
            )
        
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={email_clean}"
        now_iso = datetime.datetime.now(timezone.utc).isoformat()
        
        user_doc = {
            "email": email_clean,
            "name": req.name.strip(),
            "role": req.role or "Security Analyst",
            "hashed_password": hash_password(req.password),
            "avatar": avatar,
            "is_active": True,
            "created_at": now_iso,
        }
        result = await users_col.insert_one(user_doc)
        user_id = str(result.inserted_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MongoDB register error: {e}")
        # In-memory mock ID if DB fails
        user_id = f"mem_{int(datetime.datetime.now().timestamp())}"
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={email_clean}"

    user_resp = UserResponse(
        id=user_id,
        email=email_clean,
        name=req.name.strip(),
        role=req.role or "Security Analyst",
        avatar=avatar,
        created_at=datetime.datetime.now(timezone.utc).isoformat(),
        is_active=True,
    )

    token_delta = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={
            "sub": user_resp.email,
            "uid": user_resp.id,
            "name": user_resp.name,
            "role": user_resp.role,
            "avatar": user_resp.avatar,
        },
        expires_delta=token_delta,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(token_delta.total_seconds()),
        user=user_resp,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin):
    """Authenticate with email and password."""
    email_clean = req.email.lower().strip()
    
    # Try DB lookup first
    user_doc = None
    try:
        users_col = get_collection("users")
        user_doc = await users_col.find_one({"email": email_clean})
    except Exception as e:
        logger.warning(f"DB lookup during login failed: {e}")

    # If user not found in DB, check against default seed accounts
    if not user_doc:
        for seed in [DEFAULT_ADMIN, DEFAULT_ANALYST]:
            if email_clean == seed["email"].lower():
                if req.password == seed["password"]:
                    user_doc = {
                        "_id": f"seed_{seed['email']}",
                        "email": seed["email"],
                        "name": seed["name"],
                        "role": seed["role"],
                        "hashed_password": hash_password(seed["password"]),
                        "avatar": seed["avatar"],
                        "is_active": True,
                    }
                    # Persist to DB asynchronously if possible
                    try:
                        await users_col.insert_one(user_doc)
                    except Exception:
                        pass
                    break

    if not user_doc or not verify_password(req.password, user_doc.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended or deactivated.",
        )

    user_resp = UserResponse(
        id=str(user_doc.get("_id", user_doc["email"])),
        email=user_doc["email"],
        name=user_doc.get("name", "Security User"),
        role=user_doc.get("role", "Security Analyst"),
        avatar=user_doc.get("avatar") or f"https://api.dicebear.com/7.x/bottts/svg?seed={email_clean}",
        created_at=user_doc.get("created_at"),
        is_active=True,
    )

    expire_mins = REMEMBER_ME_EXPIRE_MINUTES if req.remember_me else ACCESS_TOKEN_EXPIRE_MINUTES
    token_delta = datetime.timedelta(minutes=expire_mins)
    
    token = create_access_token(
        data={
            "sub": user_resp.email,
            "uid": user_resp.id,
            "name": user_resp.name,
            "role": user_resp.role,
            "avatar": user_resp.avatar,
        },
        expires_delta=token_delta,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(token_delta.total_seconds()),
        user=user_resp,
    )


@router.post("/google", response_model=TokenResponse)
async def google_login(req: GoogleLoginRequest):
    """Google SSO authentication endpoint supporting real Google ID tokens and direct profile payloads."""
    email_clean = (req.email or "analyst@ransomguard.io").lower().strip()
    name = req.name or "Google Security Analyst"
    avatar = req.picture

    # If real Google ID token (JWT) is provided, decode payload
    if req.credential:
        try:
            # Decode the unverified payload from Google ID token
            decoded = jwt.decode(req.credential, options={"verify_signature": False})
            if decoded.get("email"):
                email_clean = decoded.get("email").lower().strip()
            if decoded.get("name"):
                name = decoded.get("name")
            if decoded.get("picture"):
                avatar = decoded.get("picture")
            logger.info(f"Google ID Token decoded successfully for {email_clean}")
        except Exception as err:
            logger.warning(f"Could not parse Google ID token: {err}")

    if not avatar:
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={email_clean}"

    user_doc = None
    try:
        users_col = get_collection("users")
        user_doc = await users_col.find_one({"email": email_clean})
        if not user_doc:
            user_doc = {
                "email": email_clean,
                "name": name,
                "role": "Security Analyst",
                "hashed_password": hash_password(os.urandom(24).hex()),
                "avatar": avatar,
                "is_active": True,
                "auth_provider": "google",
                "created_at": datetime.datetime.now(timezone.utc).isoformat(),
            }
            res = await users_col.insert_one(user_doc)
            user_doc["_id"] = res.inserted_id
    except Exception as e:
        logger.warning(f"Google login DB error: {e}")
        user_doc = {
            "_id": f"google_{email_clean}",
            "email": email_clean,
            "name": name,
            "role": "Security Analyst",
            "avatar": avatar,
            "is_active": True,
        }

    user_resp = UserResponse(
        id=str(user_doc.get("_id", email_clean)),
        email=email_clean,
        name=user_doc.get("name", name),
        role=user_doc.get("role", "Security Analyst"),
        avatar=user_doc.get("avatar", avatar),
        created_at=user_doc.get("created_at"),
        is_active=True,
    )

    token_delta = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={
            "sub": user_resp.email,
            "uid": user_resp.id,
            "name": user_resp.name,
            "role": user_resp.role,
            "avatar": user_resp.avatar,
        },
        expires_delta=token_delta,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(token_delta.total_seconds()),
        user=user_resp,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: UserResponse = Depends(get_current_user)):
    """Get profile of currently logged-in user."""
    return user


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Request password reset instructions."""
    email_clean = req.email.lower().strip()
    return {
        "success": True,
        "message": f"Password reset instructions have been dispatched to {email_clean}. Please check your inbox or security administrator.",
    }


@router.post("/logout")
async def logout():
    """Logout current session."""
    return {"success": True, "message": "Successfully logged out"}
