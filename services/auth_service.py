import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from services.db_service import get_user_by_username_or_email, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    # bcrypt limits password to 72 bytes
    pwd_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        plain_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def extract_token_from_request(request: Request, header_token: Optional[str] = None) -> Optional[str]:
    # Check Authorization header first
    if header_token:
        return header_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    # Check cookie fallback
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:].strip()
        return cookie_token.strip()
    return None

async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[Dict[str, Any]]:
    raw_token = extract_token_from_request(request, token)
    if not raw_token:
        return None
    payload = decode_access_token(raw_token)
    if not payload:
        return None
    username: str = payload.get("sub")
    if not username:
        return None
    user = get_user_by_username_or_email(username)
    if not user:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "created_at": user["created_at"]
    }

async def get_current_user_required(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    user = await get_current_user_optional(request, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to perform this action",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
