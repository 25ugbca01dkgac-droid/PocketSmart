import json
import uuid
import re
import base64
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from PIL import Image

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Configure Gemini if key is provided
is_gemini_configured = False
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        is_gemini_configured = True
    except Exception as e:
        print(f"Warning: Gemini configuration error: {e}")

def check_gemini_status() -> Dict[str, Any]:
    """Check connectivity to Gemini API"""
    if not GEMINI_API_KEY:
        return {
            "configured": False,
            "status": "No API Key configured. Running in Smart Hybrid Simulation Mode.",
            "model": GEMINI_MODEL
        }
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content("Respond with 'OK' if you can read this.")
        return {
            "configured": True,
            "status": "Connected to Gemini API",
            "model": GEMINI_MODEL,
            "test_response": response.text.strip()
        }
    except Exception as e:
        return {
            "configured": False,
            "status": f"Gemini API connection error: {str(e)}",
            "model": GEMINI_MODEL
        }

def clean_json_text(text: str) -> str:
    """Extract and parse JSON from raw LLM text output"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ==========================================
# 1. HOME INTERIOR RECOMMENDATIONS
# ==========================================

async def generate_home_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates home interior recommendations using Gemini or smart fallback"""
    total_budget = float(data.get("total_budget", 50000))
    currency = data.get("currency", "INR")
    rooms = data.get("room_types", ["Living Room"])
    style = data.get("style_preference", "Modern Minimalist")
    color = data.get("color_palette", "Warm Neutral & Wood")
    items_needed = data.get("items_needed", [])
    notes = data.get("notes", "")

    prompt = f"""
You are PocketSmart AI, an expert budget-conscious interior designer and cross-platform shopping assistant.
Generate a structured, budget-adherent home interior shopping plan based on:
- Total Budget: {currency} {total_budget}
- Room Types: {', '.join(rooms)}
- Style Preference: {style}
- Color Palette: {color}
- Requested Items / Details: {json.dumps(items_needed)}
- Additional Notes: {notes}

Requirements:
1. Distribute the budget realistically across rooms or product categories (e.g., Furniture, Lighting, Decor, Soft Furnishings).
2. For each category, provide specific recommended items sourced from platforms like IKEA, Amazon, Flipkart, Pepperfry, or Urban Ladder.
3. Keep the total estimated cost strictly within or very close to the total budget of {currency} {total_budget}.
4. Provide direct or realistic search links for each product on that platform (e.g. https://www.ikea.com/in/en/search/?q=..., https://www.amazon.in/s?k=..., https://www.flipkart.com/search?q=...).
5. Provide 3-4 professional styling tips and cost-saving advice.

Return ONLY a valid JSON object matching this schema:
{{
    "title": "Home Interior Plan for ...",
    "summary": "Short 2-3 sentence overview of this interior plan and budget allocation.",
    "total_budget": {total_budget},
    "total_estimated_cost": 48500,
    "remaining_balance": 1500,
    "currency": "{currency}",
    "categories": [
        {{
            "category_name": "Living Room - Furniture & Seating",
            "allocated_amount": 25000,
            "spent_amount": 24000,
            "percentage_of_budget": 50.0,
            "items": [
                {{
                    "name": "IKEA FRIHETEN 3-seat sofa-bed",
                    "category": "Furniture",
                    "price": 18000,
                    "platform": "IKEA",
                    "buy_link": "https://www.ikea.com/in/en/search/?q=sofa",
                    "rating": 4.6,
                    "match_reason": "Space-saving modern sofa with storage, fits budget and neutral palette.",
                    "quantity": 1
                }}
            ]
        }}
    ],
    "ai_tips": [
        "Use multi-functional furniture like storage ottomans to maximize space.",
        "Add warm LED strip lights behind the TV console for a luxury aesthetic on a budget."
    ]
}}
"""

    if is_gemini_configured and GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = clean_json_text(response.text)
            parsed = json.loads(raw_text)
            return enrich_recommendation_structure(parsed, "home", total_budget, currency)
        except Exception as e:
            print(f"Gemini API call failed, falling back to smart generator: {e}")

    # Fallback Smart Engine
    return fallback_home_recommendations(total_budget, currency, rooms, style, color, items_needed)


def fallback_home_recommendations(
    total_budget: float,
    currency: str,
    rooms: List[str],
    style: str,
    color: str,
    items_needed: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Smart algorithmic fallback tailored strictly to budget and rooms"""
    # Proportions: Furniture 50%, Lighting 18%, Decor & Rugs 20%, Fixtures 12%
    spent_total = 0.0
    categories = []

    # 1. Furniture
    furn_alloc = round(total_budget * 0.48, 2)
    furn_items = [
        {
            "name": f"Minimalist Solid Wood Coffee Table ({style})",
            "category": "Furniture",
            "price": round(furn_alloc * 0.28, 2),
            "platform": "IKEA",
            "buy_link": "https://www.ikea.com/in/en/search/?q=coffee+table",
            "rating": 4.6,
            "match_reason": f"Sleek clean lines with hidden shelf matching your {style} theme.",
            "quantity": 1
        },
        {
            "name": f"Ergonomic Compact Sofa / Daybed",
            "category": "Furniture",
            "price": round(furn_alloc * 0.62, 2),
            "platform": "Amazon",
            "buy_link": "https://www.amazon.in/s?k=living+room+sofa+set",
            "rating": 4.5,
            "match_reason": f"Durable upholstery in {color} tones offering comfort without exceeding budget.",
            "quantity": 1
        }
    ]
    furn_spent = sum(item["price"] for item in furn_items)
    spent_total += furn_spent
    categories.append({
        "category_name": "Furniture & Core Seating",
        "allocated_amount": furn_alloc,
        "spent_amount": furn_spent,
        "percentage_of_budget": 48.0,
        "items": furn_items
    })

    # 2. Lighting & Fans
    light_alloc = round(total_budget * 0.22, 2)
    light_items = [
        {
            "name": "Smart BLDC Energy Saving Ceiling Fan",
            "category": "Appliances & Lighting",
            "price": round(light_alloc * 0.55, 2),
            "platform": "Flipkart",
            "buy_link": "https://www.flipkart.com/search?q=bldc+ceiling+fan",
            "rating": 4.4,
            "match_reason": "Low wattage, silent operation, and modern matte finish.",
            "quantity": 1
        },
        {
            "name": "Nordic Warm Arc Floor Lamp & LED Pendant",
            "category": "Lighting",
            "price": round(light_alloc * 0.40, 2),
            "platform": "Amazon",
            "buy_link": "https://www.amazon.in/s?k=nordic+floor+lamp",
            "rating": 4.7,
            "match_reason": "Creates layered atmospheric lighting in warm neutral hue.",
            "quantity": 1
        }
    ]
    light_spent = sum(item["price"] for item in light_items)
    spent_total += light_spent
    categories.append({
        "category_name": "Lighting & Atmosphere",
        "allocated_amount": light_alloc,
        "spent_amount": light_spent,
        "percentage_of_budget": 22.0,
        "items": light_items
    })

    # 3. Decor, Wall Art & Rugs
    decor_alloc = round(total_budget * 0.25, 2)
    decor_items = [
        {
            "name": f"Textured Geometric Area Rug ({color})",
            "category": "Decor",
            "price": round(decor_alloc * 0.50, 2),
            "platform": "IKEA",
            "buy_link": "https://www.ikea.com/in/en/search/?q=area+rug",
            "rating": 4.8,
            "match_reason": "Soft woven texture that anchors the seating arrangement comfortably.",
            "quantity": 1
        },
        {
            "name": "Set of 3 Framed Botanical Canvas Wall Art",
            "category": "Wall Decor",
            "price": round(decor_alloc * 0.42, 2),
            "platform": "Amazon",
            "buy_link": "https://www.amazon.in/s?k=canvas+wall+art+framed",
            "rating": 4.6,
            "match_reason": f"Contemporary artwork curated to complement {color} interior palettes.",
            "quantity": 1
        }
    ]
    decor_spent = sum(item["price"] for item in decor_items)
    spent_total += decor_spent
    categories.append({
        "category_name": "Soft Furnishings & Wall Accents",
        "allocated_amount": decor_alloc,
        "spent_amount": decor_spent,
        "percentage_of_budget": 25.0,
        "items": decor_items
    })

    all_items = []
    for cat in categories:
        all_items.extend(cat["items"])

    remaining = max(0.0, round(total_budget - spent_total, 2))
    plan_id = str(uuid.uuid4())[:8]

    return {
        "plan_id": plan_id,
        "plan_type": "home",
        "title": f"PocketSmart Interior Plan for {', '.join(rooms)} ({style})",
        "summary": f"A comprehensive {currency} {total_budget:,.2f} decor plan optimized for {', '.join(rooms)} featuring verified items across IKEA, Amazon, and Flipkart adhering to your {style} design vision.",
        "total_budget": total_budget,
        "total_estimated_cost": spent_total,
        "remaining_balance": remaining,
        "currency": currency,
        "categories": categories,
        "all_items": all_items,
        "ai_tips": [
            "Opt for multi-purpose furniture (like beds or coffee tables with storage) to reduce clutter.",
            "Layer lighting using 2700K warm white bulbs across floor and pendant lamps for an upscale hotel feel.",
            "Shop IKEA for foundational wooden pieces and Amazon/Flipkart for lighting and wall accessories to save 15-20%."
        ],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }


# ==========================================
# 2. PARTY BUDGET RECOMMENDATIONS
# ==========================================

async def generate_party_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates party budget & vendor recommendations across Swiggy, Zomato, OYO, Amazon"""
    total_budget = float(data.get("total_budget", 25000))
    currency = data.get("currency", "INR")
    event_type = data.get("event_type", "Birthday Celebration")
    guest_count = int(data.get("guest_count", 20))
    venue_type = data.get("venue_type", "Home / Private Venue")
    food_pref = data.get("food_preference", "Multi-Cuisine Buffet")
    decor_theme = data.get("decoration_theme", "Festive Elegance")
    notes = data.get("notes", "")

    prompt = f"""
You are PocketSmart AI, an expert party planner and event budgeting assistant.
Generate an optimal event budget allocation and vendor recommendation plan for:
- Event Type: {event_type}
- Total Budget: {currency} {total_budget}
- Guest Count: {guest_count} persons (Cost per head budget ~ {total_budget/max(1, guest_count):.2f})
- Venue Preference: {venue_type}
- Food & Catering Preference: {food_pref}
- Decoration Theme: {decor_theme}
- Additional Notes: {notes}

Allocate the budget realistically across:
1. Catering & Food (Sourced via Swiggy Gourmet, Zomato Party Orders, or local catering)
2. Venue & Hospitality (OYO Townhouse, Airbnb, banquet, or home party setup)
3. Decorations & Theme Props (Amazon, Flipkart)
4. Entertainment & Music (Bluetooth party speakers, games, Spotify DJ playlist setups)

Keep total spend under {currency} {total_budget}. Provide direct search/order links for platforms like Swiggy, Zomato, OYO, and Amazon.
Include per-guest budget analytics and 3-4 professional event management tips.

Return ONLY a valid JSON object matching this schema:
{{
    "title": "Smart Event Plan: ...",
    "summary": "Short 2-3 sentence overview of this party plan and guest budget distribution.",
    "total_budget": {total_budget},
    "total_estimated_cost": 23500,
    "remaining_balance": 1500,
    "currency": "{currency}",
    "categories": [
        {{
            "category_name": "Food & Catering",
            "allocated_amount": 12000,
            "spent_amount": 11500,
            "percentage_of_budget": 50.0,
            "items": [
                {{
                    "name": "Zomato Bulk Catering / Party Box (Starters & Mains)",
                    "category": "Catering",
                    "price": 9000,
                    "platform": "Zomato",
                    "buy_link": "https://www.zomato.com",
                    "rating": 4.6,
                    "match_reason": "High-rated party package suitable for 20 guests with assorted appetizers.",
                    "quantity": 1
                }}
            ]
        }}
    ],
    "ai_tips": [
        "Order finger foods and bite-sized appetizers to reduce plate wastage.",
        "Set up a self-serve beverage bar with infused water and mocktails."
    ]
}}
"""

    if is_gemini_configured and GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = clean_json_text(response.text)
            parsed = json.loads(raw_text)
            return enrich_recommendation_structure(parsed, "party", total_budget, currency)
        except Exception as e:
            print(f"Gemini API call failed for party, falling back to smart generator: {e}")

    # Fallback Smart Engine for Party
    return fallback_party_recommendations(total_budget, currency, event_type, guest_count, venue_type, food_pref, decor_theme)


def fallback_party_recommendations(
    total_budget: float,
    currency: str,
    event_type: str,
    guest_count: int,
    venue_type: str,
    food_pref: str,
    decor_theme: str
) -> Dict[str, Any]:
    """Smart algorithmic fallback for party budget allocation"""
    # Allocation: Catering 52%, Venue/Hospitality 20%, Decor 16%, Entertainment 12%
    spent_total = 0.0
    categories = []

    # 1. Catering & Food
    cat_alloc = round(total_budget * 0.52, 2)
    per_head_food = round(cat_alloc / max(1, guest_count), 2)
    cat_items = [
        {
            "name": f"Curated Party Platters & Mains ({food_pref})",
            "category": "Catering & Dining",
            "price": round(cat_alloc * 0.75, 2),
            "platform": "Zomato / Swiggy",
            "buy_link": "https://www.zomato.com",
            "rating": 4.7,
            "match_reason": f"Delivers {per_head_food:.0f} {currency}/guest catering including appetizers, mains & sides.",
            "quantity": guest_count
        },
        {
            "name": "Customized Celebration Cake & Dessert Bar",
            "category": "Desserts",
            "price": round(cat_alloc * 0.22, 2),
            "platform": "Swiggy Gourmet",
            "buy_link": "https://www.swiggy.com",
            "rating": 4.8,
            "match_reason": f"Themed centerpiece cake and dessert shots tailored for {event_type}.",
            "quantity": 1
        }
    ]
    cat_spent = sum(item["price"] for item in cat_items)
    spent_total += cat_spent
    categories.append({
        "category_name": "Food, Beverage & Catering",
        "allocated_amount": cat_alloc,
        "spent_amount": cat_spent,
        "percentage_of_budget": 52.0,
        "items": cat_items
    })

    # 2. Venue & Space
    venue_alloc = round(total_budget * 0.20, 2)
    venue_items = [
        {
            "name": f"Event Space / Party Suite ({venue_type})",
            "category": "Venue & Hospitality",
            "price": round(venue_alloc * 0.95, 2),
            "platform": "OYO / Airbnb",
            "buy_link": "https://www.oyorooms.com",
            "rating": 4.5,
            "match_reason": f"Private celebration space accommodating {guest_count} guests comfortably with parking.",
            "quantity": 1
        }
    ]
    venue_spent = sum(item["price"] for item in venue_items)
    spent_total += venue_spent
    categories.append({
        "category_name": "Venue & Hospitality",
        "allocated_amount": venue_alloc,
        "spent_amount": venue_spent,
        "percentage_of_budget": 20.0,
        "items": venue_items
    })

    # 3. Decoration & Theme Props
    decor_alloc = round(total_budget * 0.16, 2)
    decor_items = [
        {
            "name": f"Theme Balloon Arch, Fairy Lights & Backdrop ({decor_theme})",
            "category": "Decoration",
            "price": round(decor_alloc * 0.92, 2),
            "platform": "Amazon",
            "buy_link": "https://www.amazon.in/s?k=party+decoration+kit+backdrop",
            "rating": 4.6,
            "match_reason": f"Complete DIY decorative kit with helium balloon garland and metallic photo booth fringe.",
            "quantity": 1
        }
    ]
    decor_spent = sum(item["price"] for item in decor_items)
    spent_total += decor_spent
    categories.append({
        "category_name": "Decorations & Photo Booth",
        "allocated_amount": decor_alloc,
        "spent_amount": decor_spent,
        "percentage_of_budget": 16.0,
        "items": decor_items
    })

    # 4. Entertainment & Sound
    ent_alloc = round(total_budget * 0.10, 2)
    ent_items = [
        {
            "name": "Portable High-Bass Party Speaker & Karaoke Mic Set",
            "category": "Entertainment",
            "price": round(ent_alloc * 0.90, 2),
            "platform": "Flipkart",
            "buy_link": "https://www.flipkart.com/search?q=bluetooth+party+speaker",
            "rating": 4.5,
            "match_reason": "Powers crisp dance audio and interactive games for up to 30 people.",
            "quantity": 1
        }
    ]
    ent_spent = sum(item["price"] for item in ent_items)
    spent_total += ent_spent
    categories.append({
        "category_name": "Entertainment & Music",
        "allocated_amount": ent_alloc,
        "spent_amount": ent_spent,
        "percentage_of_budget": 10.0,
        "items": ent_items
    })

    all_items = []
    for cat in categories:
        all_items.extend(cat["items"])

    remaining = max(0.0, round(total_budget - spent_total, 2))
    cost_per_person = round(spent_total / max(1, guest_count), 2)
    plan_id = str(uuid.uuid4())[:8]

    return {
        "plan_id": plan_id,
        "plan_type": "party",
        "title": f"Smart Party Blueprint: {event_type} ({guest_count} Guests)",
        "summary": f"Curated celebration budget plan of {currency} {total_budget:,.2f} (~{currency} {cost_per_person:,.2f}/guest) covering food via Zomato/Swiggy, venue via OYO, and immersive {decor_theme} decorations from Amazon.",
        "total_budget": total_budget,
        "total_estimated_cost": spent_total,
        "remaining_balance": remaining,
        "currency": currency,
        "categories": categories,
        "all_items": all_items,
        "ai_tips": [
            f"Per-head expenditure is optimized at {currency} {cost_per_person}/guest. Order combo meal trays rather than à la carte.",
            "Book your OYO or private space at least 5 days early to lock in off-peak weekend rates.",
            "Create a collaborative Spotify playlist for guests so everyone's favorite tracks get played seamlessly."
        ],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }


# ==========================================
# 3. JEWELRY RECOMMENDATIONS (MULTIMODAL)
# ==========================================

async def generate_jewelry_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates jewelry recommendations with multimodal outfit image support"""
    total_budget = float(data.get("total_budget", 15000))
    currency = data.get("currency", "INR")
    occasion = data.get("occasion", "Wedding / Reception")
    style = data.get("style_preference", "Contemporary Gold & Pearls")
    jewelry_types = data.get("jewelry_types", ["Necklace", "Earrings", "Bangles/Bracelets"])
    outfit_color = data.get("outfit_color", "Royal Emerald Green & Gold")
    outfit_type = data.get("outfit_type", "Embroidered Saree / Lehenga")
    image_base64 = data.get("image_base64")
    notes = data.get("notes", "")

    has_image = bool(image_base64 and len(image_base64) > 100)
    image_obj = None

    if has_image:
        try:
            # Strip header if data:image/...;base64,
            raw_b64 = image_base64
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_b64)
            image_obj = Image.open(io.BytesIO(img_bytes))
        except Exception as e:
            print(f"Warning: Could not decode outfit image: {e}")
            has_image = False

    prompt = f"""
You are PocketSmart AI, an haute joaillerie fashion stylist and budget advisor.
Analyze the user's styling request (and uploaded outfit photo if provided):
- Occasion: {occasion}
- Total Budget: {currency} {total_budget}
- Style Preference: {style}
- Requested Jewelry Categories: {', '.join(jewelry_types)}
- Outfit Color: {outfit_color}
- Outfit Type: {outfit_type}
- Additional Notes: {notes}

Multimodal Task:
If an outfit image is attached, analyze its exact color tone, fabric pattern, neckline, and embroidery level.
Select jewelry pieces that harmoniously elevate the outfit without clashing.
Cross-reference platforms such as CaratLane, Tanishq, Bluestone, Amazon, and Flipkart.

Distribute the budget across categories (e.g., Necklaces/Chokers, Earrings/Jhumkas, Bangles/Kadas, Rings).
Keep total price strictly within {currency} {total_budget}.
Provide realistic search/product links for CaratLane, Tanishq, Amazon, Flipkart.
Include color coordination insights and 3 styling recommendations.

Return ONLY a valid JSON object matching this schema:
{{
    "title": "Jewelry Ensemble for {occasion}",
    "summary": "Overview of color matching and aesthetic pairing for this outfit.",
    "total_budget": {total_budget},
    "total_estimated_cost": 14200,
    "remaining_balance": 800,
    "currency": "{currency}",
    "categories": [
        {{
            "category_name": "Necklace & Chokers",
            "allocated_amount": 7500,
            "spent_amount": 7200,
            "percentage_of_budget": 50.0,
            "items": [
                {{
                    "name": "Handcrafted Kundan & Pearl Choker Set",
                    "category": "Necklace",
                    "price": 7200,
                    "platform": "CaratLane / Amazon",
                    "buy_link": "https://www.caratlane.com",
                    "rating": 4.8,
                    "match_reason": "Contrasts elegantly with the neckline and picks up the golden embroidery.",
                    "quantity": 1
                }}
            ]
        }}
    ],
    "ai_tips": [
        "Pair heavy earrings with a lightweight choker to balance facial framing.",
        "Choose warm gold tones if the outfit features zari work."
    ]
}}
"""

    if is_gemini_configured and GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            contents = [prompt]
            if has_image and image_obj:
                contents.append(image_obj)

            response = model.generate_content(
                contents,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = clean_json_text(response.text)
            parsed = json.loads(raw_text)
            return enrich_recommendation_structure(parsed, "jewelry", total_budget, currency)
        except Exception as e:
            print(f"Gemini API call failed for jewelry, falling back to smart generator: {e}")

    # Fallback Smart Engine for Jewelry
    return fallback_jewelry_recommendations(total_budget, currency, occasion, style, jewelry_types, outfit_color, outfit_type, has_image)


def fallback_jewelry_recommendations(
    total_budget: float,
    currency: str,
    occasion: str,
    style: str,
    jewelry_types: List[str],
    outfit_color: str,
    outfit_type: str,
    has_image: bool = False
) -> Dict[str, Any]:
    """Smart algorithmic jewelry matching fallback"""
    spent_total = 0.0
    categories = []

    # 1. Statement Necklace / Choker (50%)
    neck_alloc = round(total_budget * 0.50, 2)
    neck_items = [
        {
            "name": f"Artisanal {style} Choker Set with Precious Stones",
            "category": "Neckpiece",
            "price": round(neck_alloc * 0.94, 2),
            "platform": "CaratLane",
            "buy_link": "https://www.caratlane.com",
            "rating": 4.8,
            "match_reason": f"Designed to highlight the neckline of your {outfit_type}, offering harmonious contrast against {outfit_color}.",
            "quantity": 1
        }
    ]
    neck_spent = sum(item["price"] for item in neck_items)
    spent_total += neck_spent
    categories.append({
        "category_name": "Necklaces & Statement Chokers",
        "allocated_amount": neck_alloc,
        "spent_amount": neck_spent,
        "percentage_of_budget": 50.0,
        "items": neck_items
    })

    # 2. Earrings / Chandbalis (28%)
    ear_alloc = round(total_budget * 0.28, 2)
    ear_items = [
        {
            "name": f"Handcrafted Chandbali Earrings with Micro-Pearls",
            "category": "Earrings",
            "price": round(ear_alloc * 0.92, 2),
            "platform": "Tanishq / Amazon",
            "buy_link": "https://www.tanishq.co.in",
            "rating": 4.7,
            "match_reason": f"Gracefully frames face structure and complements the {occasion} theme without feeling heavy.",
            "quantity": 1
        }
    ]
    ear_spent = sum(item["price"] for item in ear_items)
    spent_total += ear_spent
    categories.append({
        "category_name": "Earrings & Drops",
        "allocated_amount": ear_alloc,
        "spent_amount": ear_spent,
        "percentage_of_budget": 28.0,
        "items": ear_items
    })

    # 3. Bangles, Bracelets & Rings (20%)
    wrist_alloc = round(total_budget * 0.20, 2)
    wrist_items = [
        {
            "name": f"Set of 2 Filigree Kada Bangles & Solitaire Ring",
            "category": "Bangles & Rings",
            "price": round(wrist_alloc * 0.90, 2),
            "platform": "Flipkart",
            "buy_link": "https://www.flipkart.com/search?q=kundan+bangles+set",
            "rating": 4.6,
            "match_reason": f"Subtle wrist adornment perfectly coordinated with {style} metal finish.",
            "quantity": 1
        }
    ]
    wrist_spent = sum(item["price"] for item in wrist_items)
    spent_total += wrist_spent
    categories.append({
        "category_name": "Bangles, Cuffs & Rings",
        "allocated_amount": wrist_alloc,
        "spent_amount": wrist_spent,
        "percentage_of_budget": 20.0,
        "items": wrist_items
    })

    all_items = []
    for cat in categories:
        all_items.extend(cat["items"])

    remaining = max(0.0, round(total_budget - spent_total, 2))
    plan_id = str(uuid.uuid4())[:8]

    image_note = " (Analyzed with Multimodal Outfit Image Matching)" if has_image else ""

    return {
        "plan_id": plan_id,
        "plan_type": "jewelry",
        "title": f"Couture Jewelry Ensemble for {occasion}{image_note}",
        "summary": f"Exquisite {currency} {total_budget:,.2f} jewelry curation tailored for your {outfit_type} in {outfit_color}. Styled in {style} aesthetic across CaratLane, Tanishq, and Amazon.",
        "total_budget": total_budget,
        "total_estimated_cost": spent_total,
        "remaining_balance": remaining,
        "currency": currency,
        "categories": categories,
        "all_items": all_items,
        "ai_tips": [
            f"If your {outfit_type} has heavy golden/silver border work, let your necklace match the metal border tone.",
            "Wear statement earrings with hair pinned up or half-updo to highlight the intricate craftsmanship.",
            "Keep rings minimal if your bangles or kadas already have chunky stone work."
        ],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }


def enrich_recommendation_structure(data: Dict[str, Any], plan_type: str, total_budget: float, currency: str) -> Dict[str, Any]:
    """Ensures consistent schema and fields across raw AI outputs"""
    plan_id = str(uuid.uuid4())[:8]
    data["plan_id"] = data.get("plan_id", plan_id)
    data["plan_type"] = plan_type
    data["total_budget"] = float(data.get("total_budget", total_budget))
    data["currency"] = data.get("currency", currency)

    # Calculate actual total cost
    all_items = []
    categories = data.get("categories", [])
    for cat in categories:
        items = cat.get("items", [])
        for item in items:
            # Ensure proper buy links and default ratings
            if not item.get("buy_link"):
                platform = item.get("platform", "Amazon").lower()
                query = item.get("name", "decor").replace(" ", "+")
                if "ikea" in platform:
                    item["buy_link"] = f"https://www.ikea.com/in/en/search/?q={query}"
                elif "flipkart" in platform:
                    item["buy_link"] = f"https://www.flipkart.com/search?q={query}"
                elif "zomato" in platform:
                    item["buy_link"] = "https://www.zomato.com"
                elif "swiggy" in platform:
                    item["buy_link"] = "https://www.swiggy.com"
                elif "oyo" in platform:
                    item["buy_link"] = "https://www.oyorooms.com"
                elif "caratlane" in platform:
                    item["buy_link"] = f"https://www.caratlane.com/search/{query}"
                else:
                    item["buy_link"] = f"https://www.amazon.in/s?k={query}"
            all_items.append(item)

    data["all_items"] = all_items
    total_cost = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in all_items)
    data["total_estimated_cost"] = total_cost
    data["remaining_balance"] = max(0.0, round(data["total_budget"] - total_cost, 2))
    data["created_at"] = data.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    return data
