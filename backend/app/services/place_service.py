import sqlalchemy
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.place import Place


# =============================================================================
# 🎯 RECOMMENDATION SYSTEM (US-1.4: Dynamic Scoring & Re-ranking)
# =============================================================================

def compute_place_score(place: Place, max_views: int = 1, **kwargs) -> float:
    """
    Computes normalized recommendation score for a place (0.0 to 1.0).
    Formula: 0.6 * (rate / 5.0) + 0.4 * (view_count / max_views)
    """
    safe_rate = max(0.0, min(5.0, place.rate or 0.0))
    effective_max_views = max(1, kwargs.get("max_views", max_views) or 1)
    safe_views = max(0, place.view_count or 0)

    score = 0.6 * (safe_rate / 5.0) + 0.4 * (safe_views / effective_max_views)
    return round(min(1.0, max(0.0, score)), 4)


def recompute_scores(db: Session) -> None:
    """
    High-performance atomic SQL batch calculation:
    Updates recommendation_score for all places in a single query (<10ms).
    Triggered via POST /api/v1/places/recompute-scores or on detail view.
    """
    sql = sqlalchemy.text("""
        WITH stats AS (
            SELECT COALESCE(NULLIF(MAX(view_count), 0), 1) AS max_views
            FROM places
        )
        UPDATE places
        SET recommendation_score = ROUND(
            (
                0.6 * (COALESCE(rate, 0.0) / 5.0) +
                0.4 * (COALESCE(view_count, 0)::float / stats.max_views)
            )::numeric,
            4
        )
        FROM stats;
    """)
    db.execute(sql)
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
    Fetch a place by ID, track the view interaction, and update recommendation scores.
    """
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return None

    # Track interaction count
    place.view_count += 1
    db.commit()

    # Recompute scores dynamically so rankings adjust
    recompute_scores(db)
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
