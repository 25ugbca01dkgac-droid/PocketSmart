import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from config import HOST, PORT, DEBUG, BASE_DIR, GEMINI_API_KEY, GEMINI_MODEL
from services.db_service import init_db
from services.gemini_utils import check_gemini_status
from services.auth_service import get_current_user_optional

# Import all modular routes
from routes.auth_routes import router as auth_router
from routes.home_routes import router as home_router
from routes.party_routes import router as party_router
from routes.jewelry_routes import router as jewelry_router
from routes.history_routes import router as history_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite database and services
    print("[PocketSmart AI] Initializing services...")
    init_db()
    gemini_status = check_gemini_status()
    print(f"[Gemini AI] Status: {gemini_status['status']} (Model: {gemini_status['model']})")
    yield
    # Shutdown
    print("[PocketSmart AI] Shutting down services...")

app = FastAPI(
    title="PocketSmart AI",
    description="Your Smart Budget & Recommendation Assistant powered by Gemini 1.5 Flash Pro",
    version="1.0.0",
    lifespan=lifespan
)

# Activity 3.3: Setup CORS headers for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static and Upload directories
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
uploads_dir = BASE_DIR / "uploads"
uploads_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

templates = Jinja2Templates(directory="templates")

# Include Routers
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(party_router)
app.include_router(jewelry_router)
app.include_router(history_router)

# Activity 3.4: Startup and main page routes
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Main landing page introducing PocketSmart AI features with category selectors"""
    gemini_info = check_gemini_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user,
        "gemini_info": gemini_info
    })

@app.get("/testimonials", response_class=HTMLResponse)
async def testimonials_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Showcases real user reviews and success stories"""
    return templates.TemplateResponse("testimonials.html", {
        "request": request,
        "user": current_user
    })

@app.get("/health")
async def health_check():
    """Health and diagnostic endpoint"""
    return {
        "status": "healthy",
        "app": "PocketSmart AI",
        "version": "1.0.0",
        "gemini": check_gemini_status()
    }

# __main__: Entry point when run directly with python main.py
if __name__ == "__main__":
    print(f"[PocketSmart AI] Starting server on http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
