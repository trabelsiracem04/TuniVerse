# 🏃 Sprint 1 — Step-by-Step Plan
**Goal:** Backend foundation — DB models, data seeding, filter API, recommendation score
**Stories:** US-1.1 (filter bar backend) + US-1.4 (recommendation) + data foundation for map
**Output:** A working `GET /api/v1/places?category=&city=` API you can test in Swagger

---

## Overview

```mermaid
flowchart TD
    S1["Step 1\nInstall & Configure\nBackend"] --> S2["Step 2\nCreate Place Model\n(SQLAlchemy)"]
    S2 --> S3["Step 3\nRun Alembic\nMigration"]
    S3 --> S4["Step 4\nPydantic Schemas"]
    S4 --> S5["Step 5\nSeed the Database\n30+ Tunisian Places"]
    S5 --> S6["Step 6\nBuild Filter API\nGET /places"]
    S6 --> S7["Step 7\nRecommendation\nScore Logic"]
    S7 --> S8["Step 8\nTest in Swagger"]
```

---

## Step 1 — Install & Configure the Backend

### 1.1 Fill `requirements.txt`
Open `backend/requirements.txt` and add:
```
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic==2.10.1
pydantic-settings==2.6.1
python-dotenv==1.0.1
pgvector==0.3.6
pillow==11.0.0
```

### 1.2 Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 1.3 Fill `.env.example` → copy to `.env`
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/tuniverse
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```
Then: `cp .env.example .env` (and fill in your real Postgres credentials)

### 1.4 Fill `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 1.5 Fill `backend/app/db/session.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 1.6 Fill `backend/app/db/base.py`
```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 1.7 Boot the FastAPI app — `backend/app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TuniVerse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**✅ Check:** `uvicorn app.main:app --reload` → visit `http://localhost:8000/health`

---

## Step 2 — Create the Place Model

### 2.1 Fill `backend/app/models/place.py`
```python
from sqlalchemy import Column, Integer, String, Float, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.base import Base

class Place(Base):
    __tablename__ = "places"

    id                   = Column(Integer, primary_key=True, index=True)
    name                 = Column(String(200), nullable=False)
    city                 = Column(String(100), nullable=False, index=True)
    region               = Column(String(100), nullable=False)
    category             = Column(String(50),  nullable=False, index=True)
    sub_category         = Column(String(100), nullable=True,  index=True)
    description          = Column(Text,        nullable=False)
    short_desc           = Column(String(300), nullable=False)   # 1-line card summary
    cover_image          = Column(String(500), nullable=True)    # URL of main photo
    images               = Column(ARRAY(String), default=[])     # extra photos
    latitude             = Column(Float,       nullable=False)
    longitude            = Column(Float,       nullable=False)
    cost_estimate        = Column(String(100), nullable=True)    # e.g. "5–10 TND"
    rate                 = Column(Float,       nullable=False, default=0.0)
    view_count           = Column(Integer,     nullable=False, default=0)
    recommendation_score = Column(Float,       nullable=False, default=0.0)

    __table_args__ = (
        CheckConstraint("rate >= 0.0 AND rate <= 5.0", name="check_rate_range"),
    )
```

### 2.2 Register the model in `backend/app/db/base.py`
```python
from sqlalchemy.orm import DeclarativeBase
from app.models.place import Place   # import so Alembic sees it

class Base(DeclarativeBase):
    pass
```

> [!NOTE]
> `index=True` on `city` and `category` means DB-level indexes — filters will be fast even with thousands of places.

---

## Step 3 — Run Alembic Migration

### 3.1 Configure `alembic.ini`
In the root `backend/` folder, set:
```ini
sqlalchemy.url = postgresql://postgres:password@localhost:5432/tuniverse
```
Or better, load from env — in `backend/alembic/env.py`:
```python
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

Also in `env.py`, set target metadata:
```python
from app.db.base import Base
target_metadata = Base.metadata
```

### 3.2 Create the first migration
```bash
cd backend
alembic revision --autogenerate -m "create places table"
```

### 3.3 Apply the migration
```bash
alembic upgrade head
```

**✅ Check:** Connect to your Postgres DB and run `\dt` — you should see the `places` table.

---

## Step 4 — Pydantic Schemas

### 4.1 Fill `backend/app/schemas/place.py`
```python
from pydantic import BaseModel
from typing import Optional, List

class PlaceCard(BaseModel):
    """Minimal data for the card list and map dots"""
    id: int
    name: str
    city: str
    region: str
    category: str
    short_desc: str
    cover_image: Optional[str]
    latitude: float
    longitude: float
    recommendation_score: float

    class Config:
        from_attributes = True

class PlaceDetail(PlaceCard):
    """Full data for the detail page"""
    description: str
    images: List[str] = []
    cost_estimate: Optional[str]
    opening_hours: Optional[str]
    visit_duration: Optional[str]

class PlacesResponse(BaseModel):
    total: int
    places: List[PlaceCard]
```

---

## Step 5 — Seed the Database (30+ Tunisian Places)

### 5.1 Create `data/places_seed.json`
Collect at least 30 real places across different categories and cities.
Structure each entry like:
```json
[
  {
    "name": "Amphithéâtre d'El Jem",
    "city": "El Jem",
    "region": "Mahdia",
    "category": "monument",
    "short_desc": "One of the best-preserved Roman amphitheaters in the world.",
    "description": "The Amphitheatre of El Djem is a Roman colosseum built in 238 AD...",
    "cover_image": "https://upload.wikimedia.org/wikipedia/commons/.../El_Jem.jpg",
    "latitude": 35.2963,
    "longitude": 10.7071,
    "cost_estimate": "8 TND",
    "opening_hours": "8h–17h daily",
    "visit_duration": "1–2 hours"
  },
  {
    "name": "Medina of Tunis",
    "city": "Tunis",
    "region": "Tunis",
    "category": "monument",
    ...
  }
]
```

**Suggested places to include (mix of categories):**

| Place | City | Category |
|---|---|---|
| Amphithéâtre d'El Jem | El Jem | monument |
| Medina of Tunis | Tunis | monument |
| Carthage Ruins | Tunis | monument |
| Bardo National Museum | Tunis | museum |
| Sidi Bou Said | Tunis | cultural |
| Djerba Island | Djerba | beach |
| Hammamet Beach | Hammamet | beach |
| Sousse Medina | Sousse | monument |
| Chott el-Djerid | Tozeur | nature |
| Sahara Desert (Douz) | Douz | nature |
| Ichkeul National Park | Bizerte | nature |
| Kairouan Great Mosque | Kairouan | monument |
| Dougga Roman Site | Téboursouk | monument |
| Zarzis Beaches | Zarzis | beach |
| Korbous Hot Springs | Nabeul | wellness |

### 5.2 Create `backend/app/db/seed.py`
```python
import json
from app.db.session import SessionLocal
from app.models.place import Place

def seed():
    db = SessionLocal()
    with open("../../data/places_seed.json") as f:
        places_data = json.load(f)

    for p in places_data:
        place = Place(**p)
        db.add(place)

    db.commit()
    print(f"✅ Seeded {len(places_data)} places")
    db.close()

if __name__ == "__main__":
    seed()
```

### 5.3 Run the seed
```bash
cd backend
python -m app.db.seed
```

**✅ Check:** `SELECT COUNT(*) FROM places;` → should return 30+

---

## Step 6 — Build the Filter API Endpoint

### 6.1 Create `backend/app/services/place_service.py`
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.place import Place
from typing import Optional

def get_places(
    db: Session,
    category: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(Place)

    if category:
        query = query.filter(Place.category == category)
    if city:
        query = query.filter(Place.city == city)

    total = query.count()

    places = (
        query
        .order_by(Place.recommendation_score.desc())  # most recommended first
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, places
```

### 6.2 Create `backend/app/api/v1/places.py`
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.place import PlacesResponse, PlaceDetail
from app.services.place_service import get_places, get_place_by_id

router = APIRouter(prefix="/places", tags=["Places"])

@router.get("/", response_model=PlacesResponse)
def list_places(
    category: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    total, places = get_places(db, category=category, city=city, limit=limit, offset=offset)
    return PlacesResponse(total=total, places=places)
```

### 6.3 Register the router in `main.py`
```python
from app.api.v1.places import router as places_router

app.include_router(places_router, prefix="/api/v1")
```

**✅ Check:** `http://localhost:8000/api/v1/places?category=beach` → returns JSON list of beaches

---

## Step 7 — Recommendation Score Logic

The score combines **two signals** from the updated schema:
- `rate` — average rating (0.0–5.0), normalized → `rate / 5.0`
- `view_count` — popularity, normalized → `view_count / max_view_count`

**Formula:**

$$\text{recommendation\_score} = 0.6 \times \frac{\text{rate}}{5.0} + 0.4 \times \frac{\text{view\_count}}{\text{max\_view\_count}}$$

> This means a **highly rated place** (5★, few views) still ranks well, and a **very popular place** (many views, modest rating) also surfaces — balanced by the 60/40 weights.

### 7.1 Increment `view_count` on each detail fetch
In `backend/app/services/place_service.py`:
```python
def get_place_by_id(db: Session, place_id: int):
    place = db.query(Place).filter(Place.id == place_id).first()
    if place:
        place.view_count += 1
        db.commit()
        recompute_scores(db)   # recompute after every view
        db.refresh(place)
    return place
```

### 7.2 Recompute all scores after each view
```python
from sqlalchemy import func

def recompute_scores(db: Session):
    max_views = db.query(func.max(Place.view_count)).scalar() or 1

    places = db.query(Place).all()
    for p in places:
        normalized_rate  = (p.rate or 0.0) / 5.0
        normalized_views = p.view_count / max_views
        p.recommendation_score = round(
            0.6 * normalized_rate + 0.4 * normalized_views, 4
        )
    db.commit()
```

### 7.3 Edge cases handled
| Case | Behaviour |
|---|---|
| `rate = 0.0` (unrated, fresh place) | Score = `0.4 × popularity` only |
| `view_count = 0` (brand new place) | Score = `0.6 × (rate/5.0)` only |
| All places have 0 views | `max_views = 1` (guard against division by zero) |
| Perfect place (5★, most viewed) | Score → `1.0` |

### 7.4 Add `GET /places/:id` route
```python
@router.get("/{place_id}", response_model=PlaceDetail)
def get_place(place_id: int, db: Session = Depends(get_db)):
    place = get_place_by_id(db, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
```

---

## Step 8 — Test in Swagger

### 8.1 Open Swagger UI
```
http://localhost:8000/docs
```

### Test checklist:
- [ ] `GET /api/v1/places` → returns all 30+ places sorted by score
- [ ] `GET /api/v1/places?category=beach` → returns only beaches
- [ ] `GET /api/v1/places?city=Tunis` → returns only Tunis places
- [ ] `GET /api/v1/places?category=monument&city=Tunis` → combined filter works
- [ ] `GET /api/v1/places/{id}` → returns full detail + increments view_count
- [ ] Run the endpoint twice → `recommendation_score` updates

---

## ✅ Sprint 1 Definition of Done

| Deliverable | Done? |
|---|---|
| `requirements.txt` filled and installed | 🔲 |
| `Place` model with all fields (category, city, lat, lng, score, view_count…) | 🔲 |
| Alembic migration applied, `places` table exists in DB | 🔲 |
| `places_seed.json` with 30+ real Tunisian places | 🔲 |
| Seed script runs and DB is populated | 🔲 |
| `GET /api/v1/places` with `?category` and `?city` filters | 🔲 |
| Results sorted by `recommendation_score DESC` | 🔲 |
| `GET /api/v1/places/:id` increments `view_count` and updates score | 🔲 |
| All endpoints tested and passing in Swagger | 🔲 |

---

> [!TIP]
> Once Sprint 1 is done, Sprint 2 plugs directly into this API — the React `PlaceCardList` and Leaflet map just call `GET /api/v1/places` with filter params and render what comes back.
