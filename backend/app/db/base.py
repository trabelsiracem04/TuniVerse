from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Only import Place for Sprint 1 — add other models in later sprints
from app.models.place import Place  # noqa: E402, F401
