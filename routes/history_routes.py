from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any, List

from services.auth_service import get_current_user_optional, get_current_user_required
from services.db_service import (
    get_recommendations_by_user,
    get_recommendation_by_id,
    delete_recommendation
)

router = APIRouter(tags=["History & Dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    if not current_user:
        return RedirectResponse(url="/login?message=Please+sign+in+to+view+your+dashboard", status_code=status.HTTP_302_FOUND)

    user_id = current_user["id"]
    recommendations = get_recommendations_by_user(user_id, limit=20)

    # Calculate summary analytics
    total_plans = len(recommendations)
    total_budget_planned = sum(r["total_budget"] for r in recommendations)
    total_estimated_spend = sum(r["total_estimated_cost"] for r in recommendations)
    total_savings = max(0.0, total_budget_planned - total_estimated_spend)

    # Break down by plan type
    type_counts = {"home": 0, "party": 0, "jewelry": 0}
    for r in recommendations:
        ptype = r["plan_type"].lower()
        if ptype in type_counts:
            type_counts[ptype] += 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "recommendations": recommendations,
        "total_plans": total_plans,
        "total_budget_planned": total_budget_planned,
        "total_estimated_spend": total_estimated_spend,
        "total_savings": total_savings,
        "type_counts": type_counts
    })

@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    plan_type: Optional[str] = Query(None),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    user_id = current_user["id"] if current_user else None
    all_recs = get_recommendations_by_user(user_id, limit=50)

    if plan_type:
        all_recs = [r for r in all_recs if r["plan_type"].lower() == plan_type.lower()]

    return templates.TemplateResponse("history.html", {
        "request": request,
        "user": current_user,
        "recommendations": all_recs,
        "selected_type": plan_type
    })

@router.get("/recommendations-details", response_class=HTMLResponse)
async def recommendation_details_view(
    request: Request,
    id: int = Query(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Returns detailed AI-generated product recommendations based on user budget, preferences, and selected category"""
    rec = get_recommendation_by_id(id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation plan not found")

    plan_data = rec.get("data", {})
    plan_type = rec["plan_type"].lower()

    # Route to the appropriate visualizer template
    if plan_type == "home":
        return templates.TemplateResponse("home_recommendations.html", {
            "request": request,
            "user": current_user,
            "plan": plan_data
        })
    elif plan_type == "party":
        return templates.TemplateResponse("party_recommendations.html", {
            "request": request,
            "user": current_user,
            "plan": plan_data
        })
    elif plan_type == "jewelry":
        return templates.TemplateResponse("jewelry_recommendations.html", {
            "request": request,
            "user": current_user,
            "plan": plan_data
        })
    else:
        return templates.TemplateResponse("recommendation_detail.html", {
            "request": request,
            "user": current_user,
            "plan": plan_data,
            "rec_info": rec
        })

@router.get("/api/history")
async def api_get_history(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    user_id = current_user["id"] if current_user else None
    records = get_recommendations_by_user(user_id, limit=30)
    return {"status": "success", "count": len(records), "data": records}

@router.post("/api/history/{rec_id}/delete")
async def api_delete_history(
    rec_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_required)
):
    user_id = current_user["id"]
    success = delete_recommendation(rec_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized to delete")
    return {"status": "success", "message": f"Recommendation #{rec_id} deleted"}
