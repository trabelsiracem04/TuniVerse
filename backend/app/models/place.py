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
    short_desc           = Column(String(300), nullable=False)
    cover_image          = Column(String(500), nullable=True)
    images               = Column(ARRAY(String), default=[])
    latitude             = Column(Float,       nullable=False)
    longitude            = Column(Float,       nullable=False)
    cost_estimate        = Column(String(100), nullable=True)
    rate                 = Column(Float,       nullable=False, default=0.0)
    view_count           = Column(Integer,     nullable=False, default=0)
    recommendation_score = Column(Float,       nullable=False, default=0.0)

    __table_args__ = (
        CheckConstraint("rate >= 0.0 AND rate <= 5.0", name="check_rate_range"),
    )
