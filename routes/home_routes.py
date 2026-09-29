from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any, List
import json

from models.schemas import HomeBudgetRequest
from services.auth_service import get_current_user_optional
from services.gemini_utils import generate_home_recommendations
from services.db_service import save_recommendation, get_recommendation_by_id

router = APIRouter(tags=["Home Interior Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    return templates.TemplateResponse("home_planner.html", {
        "request": request,
        "user": current_user
    })

@router.post("/generate-home")
async def generate_home(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    # Support both JSON payload and standard form data
    data: Dict[str, Any] = {}
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        room_types = form.getlist("room_types") if hasattr(form, "getlist") else [form.get("room_types")]
        if not room_types or room_types == [None]:
            room_types = [form.get("room_type", "Living Room")]

        # Parse items and quantities
        items_needed = []
        item_names = form.getlist("item_name") if hasattr(form, "getlist") else []
        item_qtys = form.getlist("item_quantity") if hasattr(form, "getlist") else []
        for name, qty in zip(item_names, item_qtys):
            if name:
                try:
                    q = int(qty)
                except (ValueError, TypeError):
                    q = 1
                items_needed.append({"item_name": name, "quantity": q})

        data = {
            "total_budget": float(form.get("total_budget", 50000)),
            "currency": form.get("currency", "INR"),
            "room_types": room_types,
            "style_preference": form.get("style_preference", "Modern Minimalist"),
            "color_palette": form.get("color_palette", "Neutral Earth Tones"),
            "items_needed": items_needed,
            "notes": form.get("notes", "")
        }

    # Generate recommendations via Gemini / Smart AI logic
    rec_result = await generate_home_recommendations(data)

    # Save to database
    user_id = current_user["id"] if current_user else None
    rec_id = save_recommendation(
        user_id=user_id,
        plan_type="home",
        title=rec_result["title"],
        total_budget=rec_result["total_budget"],
        total_estimated_cost=rec_result["total_estimated_cost"],
        currency=rec_result["currency"],
        summary=rec_result["summary"],
        data_dict=rec_result
    )
    rec_result["db_id"] = rec_id

    # Check if client expects JSON or HTML
    accept = request.headers.get("accept", "")
    if "application/json" in accept or "application/json" in content_type:
        return JSONResponse(content=rec_result)

    return templates.TemplateResponse("home_recommendations.html", {
        "request": request,
        "user": current_user,
        "plan": rec_result
    })

@router.get("/home-recommendations", response_class=HTMLResponse)
async def home_recommendations_view(
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
        # Generate default showcase
        default_data = {
            "total_budget": 60000,
            "currency": "INR",
            "room_types": ["Living Room", "Bedroom"],
            "style_preference": "Modern Scandinavian",
            "color_palette": "Beige, Warm Oak & Sage Green"
        }
        plan = await generate_home_recommendations(default_data)

    return templates.TemplateResponse("home_recommendations.html", {
        "request": request,
        "user": current_user,
        "plan": plan
    })
