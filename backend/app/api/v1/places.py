from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.place import (
    PlaceDetail,
    PlacesResponse,
    FilterOptionsResponse,
)
from app.services.place_service import (
    get_places,
    get_place_by_id,
    get_filter_options,
    recompute_scores,
    get_similar_places,
)

router = APIRouter(prefix="/places", tags=["Places"])


@router.get("", response_model=PlacesResponse)
def list_places(
    category: Optional[str] = Query(None, description="Filter by category (e.g. accommodation, monument, beach)"),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category (e.g. hotel, roman, sandy)"),
    city: Optional[str] = Query(None, description="Filter by city/governorate (e.g. Hammamet, Tunis)"),
    search: Optional[str] = Query(None, description="Search keyword in name, short description, or city"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """
    List places filtered by category, sub-category, city, or search term.
    Results are returned sorted by recommendation score (highest first).
    """
    total, places = get_places(
        db=db,
        category=category,
        sub_category=sub_category,
        city=city,
        search=search,
        limit=limit,
        offset=offset,
    )
    return PlacesResponse(total=total, places=places)


@router.get("/filters", response_model=FilterOptionsResponse)
def list_filter_options(db: Session = Depends(get_db)):
    """
    Get all unique available categories, sub-categories, and cities for populating frontend filter selectors.
    """
    return get_filter_options(db)


@router.post("/recompute-scores")
def trigger_recompute_scores(db: Session = Depends(get_db)):
    """
    Recalculate recommendation scores for all places.
    """
    recompute_scores(db)
    return {"message": "Recommendation scores recomputed successfully"}


@router.get("/{place_id}/similar", response_model=PlacesResponse)
def similar_places(place_id: int, db: Session = Depends(get_db)):
    """
    Returns places with the same category or city, sorted by recommendation score.
    """
    similar = get_similar_places(db, place_id)
    return PlacesResponse(total=len(similar), places=similar)


@router.get("/{place_id}", response_model=PlaceDetail)
def get_place(
    place_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a single place.
    Automatically increments view_count and updates its recommendation score.
    """
    place = get_place_by_id(db=db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
