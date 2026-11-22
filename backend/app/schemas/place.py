from typing import List, Optional
from pydantic import BaseModel, Field


class PlaceCard(BaseModel):
    """Card summary view for list & map display"""
    id: int
    name: str
    city: str
    region: str
    category: str
    sub_category: Optional[str] = None
    short_desc: str
    cover_image: Optional[str] = None
    latitude: float
    longitude: float
    rate: float = Field(default=0.0, ge=0.0, le=5.0)
    view_count: int = 0
    recommendation_score: float = 0.0

    class Config:
        from_attributes = True


class PlaceDetail(PlaceCard):
    """Full detail view for single place inspection"""
    description: str
    images: List[str] = []
    cost_estimate: Optional[str] = None


class PlacesResponse(BaseModel):
    total: int
    places: List[PlaceCard]
