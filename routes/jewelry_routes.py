from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any, List
import base64

from models.schemas import JewelryBudgetRequest
from services.auth_service import get_current_user_optional
from services.gemini_utils import generate_jewelry_recommendations
from services.db_service import save_recommendation, get_recommendation_by_id

router = APIRouter(tags=["Jewelry Budget Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Jewelry budget planner page with outfit image upload"""
    return templates.TemplateResponse("jewelry_planner.html", {
        "request": request,
        "user": current_user
    })

@router.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    outfit_image: Optional[UploadFile] = File(None),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    data: Dict[str, Any] = {}
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        jewelry_types = form.getlist("jewelry_types") if hasattr(form, "getlist") else [form.get("jewelry_types")]
        if not jewelry_types or jewelry_types == [None]:
            jewelry_types = ["Necklace", "Earrings", "Bangles/Bracelets"]

        image_base64 = None
        # Handle file upload if present
        if outfit_image and outfit_image.filename:
            try:
                contents = await outfit_image.read()
                if contents:
                    encoded = base64.b64encode(contents).decode("utf-8")
                    mime = outfit_image.content_type or "image/jpeg"
                    image_base64 = f"data:{mime};base64,{encoded}"
            except Exception as e:
                print(f"Error reading uploaded outfit image: {e}")

        # Alternatively check base64 text field
        if not image_base64 and form.get("image_base64"):
            image_base64 = form.get("image_base64")

        data = {
            "total_budget": float(form.get("total_budget", 15000)),
            "currency": form.get("currency", "INR"),
            "occasion": form.get("occasion", "Wedding / Reception"),
            "style_preference": form.get("style_preference", "Contemporary Gold & Pearls"),
            "jewelry_types": jewelry_types,
            "outfit_color": form.get("outfit_color", "Emerald Green & Gold Zari"),
            "outfit_type": form.get("outfit_type", "Designer Saree / Lehenga"),
            "image_base64": image_base64,
            "notes": form.get("notes", "")
        }

    # Generate recommendations via Multimodal Gemini / Jewelry AI logic
    rec_result = await generate_jewelry_recommendations(data)

    # Save to database
    user_id = current_user["id"] if current_user else None
    rec_id = save_recommendation(
        user_id=user_id,
        plan_type="jewelry",
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

    return templates.TemplateResponse("jewelry_recommendations.html", {
        "request": request,
        "user": current_user,
        "plan": rec_result
    })

@router.get("/jewelry-recommendations", response_class=HTMLResponse)
async def jewelry_recommendations_view(
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
            "total_budget": 20000,
            "currency": "INR",
            "occasion": "Festive Diwali / Reception",
            "style_preference": "Temple Jewelry in Matte Antique Gold",
            "outfit_color": "Crimson Red with Golden Embroidery",
            "outfit_type": "Silk Kanjeevaram Saree"
        }
        plan = await generate_jewelry_recommendations(default_data)

    return templates.TemplateResponse("jewelry_recommendations.html", {
        "request": request,
        "user": current_user,
        "plan": plan
    })
