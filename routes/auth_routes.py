from fastapi import APIRouter, Request, Response, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any

from models.schemas import UserRegister, UserLogin, Token, SessionInfo
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
    get_current_user_required
)
from services.db_service import (
    create_user,
    get_user_by_username_or_email,
    get_recommendations_by_user
)

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

# --- UI Pages ---

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "user": current_user,
        "error": None
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "user": current_user,
        "error": None
    })

@router.get("/logout")
async def logout(response: Response):
    res = RedirectResponse(url="/login?message=Logged+out+successfully", status_code=status.HTTP_302_FOUND)
    res.delete_cookie(key="access_token", path="/")
    return res


# --- API Endpoints ---

@router.post("/register")
async def register_user(
    request: Request,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    password: Optional[str] = Form(None)
):
    # Support both JSON payload and standard form data
    if not username:
        try:
            body = await request.json()
            username = body.get("username")
            email = body.get("email")
            full_name = body.get("full_name")
            password = body.get("password")
        except Exception:
            pass

    is_api_request = "application/json" in request.headers.get("accept", "") or "application/json" in request.headers.get("content-type", "")

    if not username or not email or not password:
        err = "Username, email, and password are all required."
        if is_api_request:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": err}, status_code=400)

    if len(password) < 6:
        err = "Password must be at least 6 characters long."
        if is_api_request:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": err}, status_code=400)

    existing = get_user_by_username_or_email(username)
    if existing:
        err = "Username or email is already registered."
        if is_api_request:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": err}, status_code=400)

    pwd_hash = hash_password(password)
    user = create_user(username=username, email=email, password_hash=pwd_hash, full_name=full_name)
    if not user:
        err = "Registration failed. Please try a different username/email."
        if is_api_request:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": err}, status_code=400)

    # Issue JWT token
    token = create_access_token({"sub": user["username"], "user_id": user["id"]})

    if is_api_request:
        return {
            "status": "success",
            "message": "User registered successfully",
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }

    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, max_age=86400, path="/")
    return redirect

@router.post("/login")
async def login_user(
    request: Request,
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None)
):
    # Support both JSON payload and form data
    if not username:
        try:
            body = await request.json()
            username = body.get("username") or body.get("username_or_email")
            password = body.get("password")
        except Exception:
            pass

    is_api_request = "application/json" in request.headers.get("accept", "") or "application/json" in request.headers.get("content-type", "")

    if not username or not password:
        err = "Username and password are required."
        if is_api_request:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("login.html", {"request": request, "user": None, "error": err}, status_code=400)

    user = get_user_by_username_or_email(username)
    if not user or not verify_password(password, user["password_hash"]):
        err = "Invalid username/email or password."
        if is_api_request:
            raise HTTPException(status_code=401, detail=err)
        return templates.TemplateResponse("login.html", {"request": request, "user": None, "error": err}, status_code=401)

    # Token generation
    token = create_access_token({"sub": user["username"], "user_id": user["id"]})

    if is_api_request:
        return {
            "status": "success",
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user.get("full_name")
            }
        }

    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, max_age=86400, path="/")
    return redirect

@router.post("/token", response_model=Token)
async def login_for_access_token(request: Request):
    """OAuth2 compatible token endpoint"""
    try:
        data = await request.form()
        username = data.get("username")
        password = data.get("password")
    except Exception:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")

    user = get_user_by_username_or_email(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user["username"], "user_id": user["id"]})
    return {"access_token": token, "token_type": "bearer", "username": user["username"]}

@router.get("/session-info")
async def get_session_info(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Returns basic session metadata"""
    if current_user:
        return {
            "authenticated": True,
            "user": current_user,
            "status": "active"
        }
    return {
        "authenticated": False,
        "user": None,
        "status": "anonymous"
    }

@router.get("/session-data")
async def get_session_data(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Returns detailed session personalization and recommendation tracking"""
    user_id = current_user["id"] if current_user else None
    recent_recs = get_recommendations_by_user(user_id, limit=5)
    
    return {
        "authenticated": bool(current_user),
        "user": current_user,
        "recommendation_count": len(recent_recs),
        "recent_plans": [
            {
                "id": r["id"],
                "plan_type": r["plan_type"],
                "title": r["title"],
                "total_budget": r["total_budget"],
                "currency": r["currency"],
                "created_at": r["created_at"]
            }
            for r in recent_recs
        ]
    }
