"""
Seed Hotels into Supabase PostgreSQL (places table).
Reads data/processed/hotels.json and inserts/updates records.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy.dialects.postgresql import insert

def seed_hotels():
    # 1. Load environment and database URL
    env_path = Path(__file__).resolve().parent.parent.parent / "backend" / ".env"
    load_dotenv(env_path)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in backend/.env")
        return

    # 2. Load processed hotels
    hotels_file = Path(__file__).resolve().parent.parent / "processed" / "hotels.json"
    if not hotels_file.exists():
        print(f"❌ File not found: {hotels_file}")
        return

    with open(hotels_file, "r", encoding="utf-8") as f:
        hotels = json.load(f)

    print(f"📦 Loaded {len(hotels)} hotels from {hotels_file.name}")

    # 3. Connect to database
    engine = sqlalchemy.create_engine(db_url)
    metadata = sqlalchemy.MetaData()
    places_table = sqlalchemy.Table("places", metadata, autoload_with=engine)

    print("🚀 Connecting to Supabase and seeding hotels...")

    with engine.begin() as conn:
        for hotel in hotels:
            # Prepare upsert statement
            stmt = insert(places_table).values(
                id=hotel["id"],
                name=hotel["name"],
                city=hotel["city"],
                region=hotel["region"],
                category=hotel["category"],
                sub_category=hotel.get("sub_category"),
                description=hotel["description"],
                short_desc=hotel["short_desc"],
                cover_image=hotel.get("cover_image"),
                images=hotel.get("images", []),
                latitude=hotel["latitude"],
                longitude=hotel["longitude"],
                cost_estimate=hotel.get("cost_estimate"),
                view_count=hotel.get("view_count", 0),
                rate=hotel["rate"],
                recommendation_score=hotel["recommendation_score"]
            )
            # If id already exists, update all fields
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": stmt.excluded.name,
                    "city": stmt.excluded.city,
                    "region": stmt.excluded.region,
                    "category": stmt.excluded.category,
                    "sub_category": stmt.excluded.sub_category,
                    "description": stmt.excluded.description,
                    "short_desc": stmt.excluded.short_desc,
                    "cover_image": stmt.excluded.cover_image,
                    "images": stmt.excluded.images,
                    "latitude": stmt.excluded.latitude,
                    "longitude": stmt.excluded.longitude,
                    "cost_estimate": stmt.excluded.cost_estimate,
                    "view_count": stmt.excluded.view_count,
                    "rate": stmt.excluded.rate,
                    "recommendation_score": stmt.excluded.recommendation_score
                }
            )
            conn.execute(stmt)

    # 4. Verify insertion
    with engine.connect() as conn:
        count = conn.execute(
            sqlalchemy.text("SELECT count(*) FROM places WHERE category = 'accommodation';")
        ).scalar()
        print(f"✅ Successfully seeded! Total accommodations in Supabase: {count}")

if __name__ == "__main__":
    seed_hotels()
