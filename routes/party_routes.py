from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any

from models.schemas import PartyBudgetRequest
from services.auth_service import get_current_user_optional
from services.gemini_utils import generate_party_recommendations
from services.db_service import save_recommendation, get_recommendation_by_id

router = APIRouter(tags=["Party Budget Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    return templates.TemplateResponse("party_planner.html", {
        "request": request,
        "user": current_user
    })

@router.post("/generate-party")
async def generate_party(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    data: Dict[str, Any] = {}
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = {
            "total_budget": float(form.get("total_budget", 25000)),
            "currency": form.get("currency", "INR"),
            "event_type": form.get("event_type", "Birthday Celebration"),
            "guest_count": int(form.get("guest_count", 20)),
            "venue_type": form.get("venue_type", "Home / Private Venue"),
            "food_preference": form.get("food_preference", "Multi-Cuisine Buffet"),
            "decoration_theme": form.get("decoration_theme", "Festive Elegance"),
            "entertainment_needed": form.get("entertainment_needed") in ("true", "on", "yes", True),
            "notes": form.get("notes", "")
        }

    # Generate recommendations via Gemini / Party AI logic
    rec_result = await generate_party_recommendations(data)

    # Save to database
    user_id = current_user["id"] if current_user else None
    rec_id = save_recommendation(
        user_id=user_id,
        plan_type="party",
        title=rec_result["title"],
        total_budget=rec_result["total_budget"],
        total_estimated_cost=rec_result["total_estimated_cost"],
        currency=rec_result["currency"],
        summary=rec_result["summary"],
        data_dict=rec_result
    )
    rec_result["db_id"] = rec_id

    accept = request.headers.get("accept", "")
    if "application/json" in accept or "application/json" in content_type:
        return JSONResponse(content=rec_result)

    return templates.TemplateResponse("party_recommendations.html", {
        "request": request,
        "user": current_user,
        "plan": rec_result
    })

@router.get("/party-recommendations", response_class=HTMLResponse)
async def party_recommendations_view(
    request: Request,
    id: Optional[int] = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    plan = None
    if id:
        db_rec = get_recommendation_by_id(id)
        if db_rec:
            plan = db_rec.get("data")
            if plan:
                plan["db_id"] = id

    if not plan:
        default_data = {
            "total_budget": 30000,
            "currency": "INR",
            "event_type": "Cocktail & Birthday Bash",
            "guest_count": 25,
            "venue_type": "Private Terrace / OYO Suite",
            "food_preference": "Starters & Continental Buffet",
            "decoration_theme": "Golden Fairy Lights & Minimalist Chic"
        }
        plan = await generate_party_recommendations(default_data)

    return templates.TemplateResponse("party_recommendations.html", {
        "request": request,
        "user": current_user,
        "plan": plan
    })
