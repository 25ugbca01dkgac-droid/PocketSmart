# ⚡ PocketSmart AI: Your Smart Budget & Recommendation Assistant

> **GenAI-powered, cross-platform budget and lifestyle recommendation assistant** built with **FastAPI** and **Google Gemini 1.5 Flash Pro**.

PocketSmart AI bridges multi-category lifestyle needs—such as interior design, event celebrations, and occasion jewelry—with intelligent, budget-strict recommendations sourced across trusted e-commerce ecosystems including **Amazon, Flipkart, IKEA, Swiggy, Zomato, and OYO**.

---

## 🌟 Key Scenarios & Capabilities

### 🛋️ Scenario 1: Home Interior Planning with Smart Budget Allocation
- **Input Parameters:** Target budget (INR), room selection (*Living Room, Kitchen, Master Bedroom, Dining, Balcony, Study*), interior style aesthetic (*Modern Minimalist, Scandinavian Oak, Industrial, Heritage, Bohemian*), color palette, and dynamic item requirements (*ceiling fans, lights, coffee tables, sofa sets*).
- **AI Recommendation Engine:** Proportional budget allocation across core furniture (48%), lighting and climate fixtures (22%), soft furnishings and wall accents (25%). Curated product options from **IKEA**, **Amazon**, and **Flipkart** with direct search and purchase links, item pricing, user ratings, and expert interior styling tips.

### 🎉 Scenario 2: AI-Based Party Budget Planning
- **Input Parameters:** Total celebration budget, guest count, event type (*Birthday, Wedding Reception, Cocktail, Corporate Mixer, Anniversary*), venue preference (*OYO Suite, Home Terrace, Banquet*), and catering style.
- **AI Recommendation Engine:** Allocates funds proportionally across Catering (**Zomato / Swiggy Gourmet**), Venue hospitality (**OYO Townhouse / Airbnb**), Theme props and photo booth sets (**Amazon**), and DJ sound/karaoke equipment (**Flipkart**). Calculates exact per-guest expenditure and provides crowd-management advice.

### 💎 Scenario 3: Occasion Jewelry Recommendations (Multimodal Vision)
- **Input Parameters:** Total jewelry budget, occasion (*Wedding, Reception, Festive Diwali, Cocktail Gala*), aesthetic preference (*Antique Temple Gold, Royal Kundan, Minimalist American Diamond, Bohemian Silver*), desired pieces (*Necklaces, Earrings/Jhumkas, Bangles/Kadas, Rings*), and **optional outfit image upload**.
- **Multimodal AI Analysis:** Gemini 1.5 Flash Pro visually examines uploaded outfit photos for exact fabric hues, necklines, and embroidery accents to match jewelry sets from **CaratLane, Tanishq, Amazon, and Flipkart**.

---

## 🏗️ Architecture & Modular Structure

```
d:/PocketSmart/
├── .env                         # Active environment configuration
├── .env.example                 # Template for environment settings
├── .gitignore                   # Version control ignore list
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation & setup guide
├── main.py                      # FastAPI app entry point (Lifespan, CORS, Static/Upload mount)
├── config.py                    # Environment and path settings
├── models/
│   ├── __init__.py
│   └── schemas.py               # Pydantic data schemas (Home, Party, Jewelry, Auth, History)
├── services/
│   ├── __init__.py
│   ├── db_service.py            # SQLite database service (users, recommendations, sessions)
│   ├── auth_service.py          # Bcrypt hashing & JWT authentication
│   └── gemini_utils.py          # Gemini 1.5 Flash Pro integration & Smart Hybrid Fallback
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py           # /login, /register, /logout, /token, /session-info, /session-data
│   ├── home_routes.py           # /home-planner, /generate-home, /home-recommendations
│   ├── party_routes.py          # /party-planner, /generate-party, /party-recommendations
│   ├── jewelry_routes.py        # /jewelry-planner, /generate-jewelry, /jewelry-recommendations
│   └── history_routes.py        # /dashboard, /history, /recommendations-details, /api/history
├── templates/
│   ├── base.html                # Master layout with Glassmorphism navigation & footer
│   ├── index.html               # Main landing page with hero & planner category cards
│   ├── testimonials.html        # Real user reviews and success stories
│   ├── login.html               # User sign-in interface
│   ├── register.html            # User registration interface
│   ├── dashboard.html           # User dashboard with recent activity & budget analytics
│   ├── home_planner.html        # Scenario 1 input form
│   ├── home_recommendations.html# Scenario 1 recommendation results
│   ├── party_planner.html       # Scenario 2 input form
│   ├── party_recommendations.html # Scenario 2 recommendation results
│   ├── jewelry_planner.html     # Scenario 3 input form with outfit image dropzone
│   ├── jewelry_recommendations.html # Scenario 3 recommendation results
│   ├── history.html             # History log with filters and plan viewers
│   └── recommendation_detail.html # Generic plan detail visualizer
├── static/
│   ├── css/
│   │   └── style.css            # Custom Glassmorphism design system & micro-animations
│   └── js/
│       └── main.js              # Live budget slider sync, dynamic rows, drag-and-drop image upload
├── uploads/                     # Storage for user-uploaded outfit images
└── tests/
    ├── __init__.py
    └── test_app.py              # Automated Pytest suite (Auth, Planners, History, API endpoints)
```

---

## 🚀 Quick Start Guide (VS Code Setup)

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12.6)
- **VS Code** with the **Python** extension installed

### 2. Open Project in VS Code
Open VS Code and navigate to the project directory:
```bash
code d:/PocketSmart
```

### 3. Create & Activate Virtual Environment (Optional but Recommended)
In VS Code Terminal (`Ctrl + ~`):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and configure your Google Gemini API key:
```ini
# Get your free API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSyYourActualKeyHere
GEMINI_MODEL=gemini-1.5-flash
SECRET_KEY=pocketsmart_super_secure_key_2026
```

> **Smart Hybrid Simulation Mode:** If `GEMINI_API_KEY` is not provided or if the API hits temporary quota limits, the application automatically activates its **Smart Hybrid Recommendation Engine**. It calculates real budget splits and realistic product items across Amazon, IKEA, Flipkart, Swiggy, Zomato, and OYO so the app remains 100% operational for evaluation and demos!

---

## 🏃 Running the Application

### Option A: Direct Python Run
```powershell
python main.py
```

### Option B: Using Uvicorn with Hot Reload
```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Once started, open your web browser:
- 🌐 **Web Interface:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📑 **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Running Automated Tests

Run the comprehensive pytest suite:
```powershell
pytest -v tests/test_app.py
```

**Test Coverage Highlights:**
- `test_health_check`: Validates system status and Gemini connectivity.
- `test_landing_and_public_pages`: Checks HTML rendering of landing, planners, and testimonials.
- `test_user_registration_and_login`: Tests bcrypt password encryption, JWT issuance, and session verification.
- `test_generate_home_recommendations_api`: Tests Scenario 1 Home Interior budget calculation.
- `test_generate_party_recommendations_api`: Tests Scenario 2 Party catering and venue allocation.
- `test_generate_jewelry_recommendations_api`: Tests Scenario 3 Jewelry style curation.
- `test_history_and_details`: Tests persistent SQLite history saving and retrieval.

---

## 🛡️ Authentication & Session Management
- **Registration:** Accessible at `/register` or via `POST /register`
- **Login:** Accessible at `/login` or via `POST /login`
- **JWT Token Endpoint:** `POST /token` (OAuth2 compatible)
- **Session Introspection:** `GET /session-info` and `GET /session-data`
- **Personal Dashboard:** Accessible at `/dashboard` displaying metrics, savings calculations, and past plans.
---

## 📜 License
Developed with Google Gemini 1.5 Flash Pro & FastAPI for the PocketSmart AI project. All rights reserved.
