from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.place import Place


# =============================================================================
# 🎯 RECOMMENDATION SYSTEM PLACEHOLDERS (Assigned to Teammate)
# =============================================================================

def compute_place_score(place: Place, **kwargs) -> float:
    """
    TODO: [Recommendation System] Single Place Score Calculation
    -------------------------------------------------------------
    Author / Assignee: Teammate
    
    Inputs available on `place`:
      - place.id: int
      - place.name: str
      - place.rate: float (0.0 to 5.0)
      - place.view_count: int (number of views/clicks)
      - place.category: str (e.g. 'accommodation', 'monument', 'beach')
      - place.sub_category: str (e.g. 'hotel', 'roman')
      - place.city: str (e.g. 'Hammamet', 'Tunis')
      - kwargs: Optional user context (user_id, preferences, session data)

    Expected Output:
      - float: Normalized score (typically 0.0 to 1.0) used to rank places.
    """
    # -------------------------------------------------------------------------
    # >>> WRITE YOUR RECOMMENDATION ALGORITHM / FORMULA HERE <<<
    #
    # Example ideas:
    # 1. Hybrid Score:
    #    score = (0.7 * (place.rate / 5.0)) + (0.3 * (place.view_count / max_views))
    # 2. Collaborative Filtering or Matrix Factorization
    # 3. Content-Based matching using place category & user profile
    # -------------------------------------------------------------------------

    # Default placeholder: uses rating as a neutral baseline
    return round((place.rate or 0.0) / 5.0, 4)


def recompute_scores(db: Session) -> None:
    """
    TODO: [Recommendation System] Batch Recomputation
    -------------------------------------------------------------
    Author / Assignee: Teammate

    Triggered via POST /api/v1/places/recompute-scores or scheduled background job.
    Updates `recommendation_score` for all places in the database.
    """
    places = db.query(Place).all()

    # -------------------------------------------------------------------------
    # >>> WRITE YOUR BATCH UPDATE LOGIC HERE <<<
    # -------------------------------------------------------------------------
    for p in places:
        p.recommendation_score = compute_place_score(p)

    db.commit()


# =============================================================================
# 🔍 CORE RETRIEVAL & FILTERING QUERIES
# =============================================================================

def get_places(
    db: Session,
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[int, List[Place]]:
    """
    List places filtered by category, sub_category, city, or search term.
    Results are ordered by recommendation_score DESC, then rate DESC.
    """
    query = db.query(Place)

    if category:
        query = query.filter(func.lower(Place.category) == category.strip().lower())
    if sub_category:
        query = query.filter(func.lower(Place.sub_category) == sub_category.strip().lower())
    if city:
        query = query.filter(func.lower(Place.city) == city.strip().lower())
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            (func.lower(Place.name).like(search_pattern))
            | (func.lower(Place.short_desc).like(search_pattern))
            | (func.lower(Place.city).like(search_pattern))
        )

    total = query.count()

    places = (
        query.order_by(Place.recommendation_score.desc(), Place.rate.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, places


def get_place_by_id(db: Session, place_id: int) -> Optional[Place]:
    """
    Fetch a place by ID, track the view interaction, and update recommendation score.
    """
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return None

    # Track interaction count
    place.view_count += 1

    # -------------------------------------------------------------------------
    # Re-score this place based on the new interaction event
    # -------------------------------------------------------------------------
    place.recommendation_score = compute_place_score(place)

    db.commit()
    db.refresh(place)
    return place


def get_filter_options(db: Session) -> dict:
    """
    Return distinct categories, sub-categories, and cities to populate frontend filter dropdowns.
    """
    cities = [r[0] for r in db.query(Place.city).distinct().order_by(Place.city).all() if r[0]]
    categories = [r[0] for r in db.query(Place.category).distinct().order_by(Place.category).all() if r[0]]
    sub_categories = [r[0] for r in db.query(Place.sub_category).distinct().order_by(Place.sub_category).all() if r[0]]
    return {
        "cities": cities,
        "categories": categories,
        "sub_categories": sub_categories,
    }
