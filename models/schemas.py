from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# --- Authentication Schemas ---

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: str

class SessionInfo(BaseModel):
    authenticated: bool
    user: Optional[UserOut] = None
    session_id: Optional[str] = None


# --- Home Interior Budget Schemas ---

class RoomItemRequirement(BaseModel):
    item_name: str
    quantity: int = 1
    priority: Optional[str] = "High"  # High, Medium, Low

class HomeBudgetRequest(BaseModel):
    total_budget: float = Field(..., gt=0, description="Total budget in INR or USD")
    currency: str = Field("INR", description="Currency symbol/code, e.g. INR, USD")
    room_types: List[str] = Field(..., description="e.g. Living Room, Bedroom, Kitchen, Balcony")
    style_preference: str = Field("Modern Minimalist", description="e.g. Modern, Scandinavian, Industrial, Traditional, Bohemian")
    color_palette: Optional[str] = Field(None, description="Preferred colors, e.g. Warm Earthy, Monochrome, Pastel")
    items_needed: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, 
        description="List of specific items like lights, ceiling fans, dining tables, sofa, rugs"
    )
    notes: Optional[str] = None


# --- Party Budget Schemas ---

class PartyBudgetRequest(BaseModel):
    total_budget: float = Field(..., gt=0, description="Total budget in INR")
    currency: str = Field("INR", description="Currency symbol/code")
    event_type: str = Field(..., description="e.g. Birthday, Anniversary, Wedding, Corporate, House Party, Farewell")
    guest_count: int = Field(..., gt=0, description="Number of anticipated guests")
    venue_type: str = Field("Home / Private Venue", description="e.g. Home, Banquet Hall, OYO/Hotel, Outdoor Garden")
    food_preference: str = Field("Multi-Cuisine Buffet", description="e.g. Veg Buffet, Non-Veg Buffet, Finger Food & Snacks, Continental")
    entertainment_needed: bool = Field(True, description="Whether DJ, sound system, or games are required")
    decoration_theme: Optional[str] = Field(None, description="e.g. Neon, Floral, Minimalist Elegance, Retro")
    notes: Optional[str] = None


# --- Jewelry Budget Schemas ---

class JewelryBudgetRequest(BaseModel):
    total_budget: float = Field(..., gt=0, description="Total budget in INR")
    currency: str = Field("INR", description="Currency code")
    occasion: str = Field(..., description="e.g. Wedding, Festive / Diwali, Cocktail Party, Office Wear, Casual Daily")
    style_preference: str = Field("Contemporary Gold & Pearls", description="e.g. Antique Temple, Minimalist Diamond, Kundan, Bohemian Silver, Rose Gold")
    jewelry_types: List[str] = Field(default_factory=lambda: ["Necklace", "Earrings", "Bangles/Bracelets"], description="Categories desired")
    outfit_color: Optional[str] = Field(None, description="Color of the outfit if image not uploaded")
    outfit_type: Optional[str] = Field(None, description="e.g. Saree, Lehenga, Evening Gown, Indo-Western, Suit")
    image_base64: Optional[str] = Field(None, description="Base64 encoded outfit photo for multimodal analysis")
    notes: Optional[str] = None


# --- Output Recommendation Schemas ---

class ProductItem(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    price: float
    platform: str  # Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, CaratLane, Tanishq, etc.
    platform_icon: Optional[str] = None
    buy_link: str
    image_url: Optional[str] = None
    rating: Optional[float] = 4.5
    match_reason: str
    quantity: int = 1

class CategoryBudgetBreakdown(BaseModel):
    category_name: str
    allocated_amount: float
    spent_amount: float
    percentage_of_budget: float
    items: List[ProductItem]

class RecommendationResponse(BaseModel):
    plan_id: str
    plan_type: str  # home, party, jewelry
    title: str
    summary: str
    total_budget: float
    total_estimated_cost: float
    remaining_balance: float
    currency: str = "INR"
    categories: List[CategoryBudgetBreakdown]
    all_items: List[ProductItem]
    ai_tips: List[str]
    created_at: str


# --- History Schema ---

class HistoryItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    plan_type: str
    title: str
    total_budget: float
    total_estimated_cost: float
    currency: str
    summary: str
    data_json: str
    created_at: str
