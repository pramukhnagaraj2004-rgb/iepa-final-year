import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt, JWTError
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from authlib.integrations.starlette_client import OAuth

# Load environment variables from both root and iepa/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
env_root = PROJECT_ROOT / ".env"
env_iepa = PROJECT_ROOT / "iepa" / ".env"
if env_iepa.exists():
    load_dotenv(dotenv_path=env_iepa, override=True)
if env_root.exists():
    load_dotenv(dotenv_path=env_root, override=False)

GOOGLE_CLIENT_ID     = (os.getenv("GOOGLE_CLIENT_ID", "") or "").strip().replace("\n", "").replace("\r", "").replace(" ", "")
GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET", "") or "").strip()
JWT_SECRET           = (os.getenv("JWT_SECRET", "70177bf7e630d57d198b3a0fd97b573a715922ac00cd6431f763559826afcbb6") or "").strip()
FRONTEND_URL         = (os.getenv("FRONTEND_URL", "http://localhost:3000") or "").rstrip("/")
JWT_ALGORITHM        = "HS256"
JWT_EXPIRATION_DAYS  = 7

# OAuth Client setup
oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"}
    )

# HTTP Bearer Security scheme
http_bearer = HTTPBearer(auto_error=False)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates signed JWT token with standard payload and expiration.
    """
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(days=JWT_EXPIRATION_DAYS)
        
    to_encode.update({"exp": expire, "iat": now_utc})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and verifies a JWT token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and authenticate the current user from Bearer JWT.
    Raises 401 if missing, invalid, or expired.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials were not provided"
        )
        
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or malformed authentication token"
        )
        
    google_id = payload.get("sub")
    email = payload.get("email")
    if not google_id and not email:
        raise HTTPException(
            status_code=401,
            detail="Token payload is missing user identity"
        )

    # Attempt to fetch live user data from Mongo
    try:
        from iepa.backend.db.mongo import get_user, get_user_by_email
        db_user = await get_user(google_id) if google_id else None
        if not db_user and email:
            db_user = await get_user_by_email(email)
            
        if db_user:
            return db_user
    except Exception as e:
        print(f"[!] Mongo user lookup warning: {e}")

    # Fallback to payload data if DB is offline or user not cached
    return {
        "google_id": google_id or email,
        "email": email or "",
        "name": payload.get("name", "Student"),
        "picture": payload.get("picture", ""),
        "tier": payload.get("tier", "free"),
        "analyses_this_month": payload.get("analyses_this_month", 0)
    }

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for endpoints that accept optional authentication.
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

if __name__ == "__main__":
    print("=== Testing JWT Creation & Decoding in Isolation ===")
    sample_user = {
        "sub": "google_test_12345",
        "email": "student@sjbit.edu.in",
        "name": "Alex Student",
        "tier": "free"
    }
    
    token = create_access_token(sample_user)
    print("Created JWT:", token[:30] + "...")
    
    decoded = decode_access_token(token)
    print("Decoded payload:", decoded)
    assert decoded["sub"] == sample_user["sub"]
    assert decoded["email"] == sample_user["email"]
    assert "exp" in decoded
    
    # Test invalid token
    invalid_decode = decode_access_token("invalid.token.structure")
    assert invalid_decode is None
    print("[+] JWT authentication functions verified successfully!")
