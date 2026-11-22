"""
seed_database.py

Universal database seeder for Supabase PostgreSQL (places table).
Can seed hotels, attractions, or the complete unified master catalog.

Usage:
  python data/scripts/seed_database.py                 (Seeds the complete master dataset: 1,807 places)
  python data/scripts/seed_database.py --hotels        (Seeds only accommodations: 117 hotels)
  python data/scripts/seed_database.py --attractions   (Seeds only tourist attractions: 1,690 places)
"""
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy.dialects.postgresql import insert

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

PROCESSED_DIR = ROOT_DIR / "data" / "processed"


def seed_places(target_file: Path, description: str):
    env_path = ROOT_DIR / "backend" / ".env"
    load_dotenv(env_path)
    root_env = ROOT_DIR / ".env"
    load_dotenv(root_env)

    import os
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in backend/.env")
        return

    if not target_file.exists():
        print(f"❌ File not found: {target_file}")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        places_data = json.load(f)

    print(f"📦 Loaded {len(places_data)} records for {description} from {target_file.name}")

    engine = sqlalchemy.create_engine(db_url)
    metadata = sqlalchemy.MetaData()
    places_table = sqlalchemy.Table("places", metadata, autoload_with=engine)

    print(f"🚀 Upserting {len(places_data)} records into Supabase PostgreSQL...")

    batch_size = 200
    with engine.begin() as conn:
        for i in range(0, len(places_data), batch_size):
            batch = places_data[i:i + batch_size]
            for p in batch:
                stmt = insert(places_table).values(
                    id=p["id"],
                    name=p["name"],
                    city=p["city"],
                    region=p["region"],
                    category=p["category"],
                    sub_category=p.get("sub_category"),
                    description=p["description"],
                    short_desc=p["short_desc"],
                    cover_image=p.get("cover_image"),
                    images=p.get("images", []),
                    latitude=p["latitude"],
                    longitude=p["longitude"],
                    cost_estimate=p.get("cost_estimate"),
                    view_count=p.get("view_count", 0),
                    rate=p["rate"],
                    recommendation_score=p["recommendation_score"]
                )
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
            print(f"  ⚡ Upserted batch {i + 1} - {min(i + batch_size, len(places_data))} / {len(places_data)}")

    # Verification query
    with engine.connect() as conn:
        total_count = conn.execute(sqlalchemy.text("SELECT count(*) FROM places;")).scalar()
        acc_count = conn.execute(sqlalchemy.text("SELECT count(*) FROM places WHERE category = 'accommodation';")).scalar()
        att_count = conn.execute(sqlalchemy.text("SELECT count(*) FROM places WHERE category != 'accommodation';")).scalar()
        print("\n" + "─" * 60)
        print("✅ Seeding successfully completed!")
        print(f"📊 Total places in Supabase: {total_count}")
        print(f"🏨 Accommodations (Hotels): {acc_count}")
        print(f"🏛️ Tourist Attractions:     {att_count}")


if __name__ == "__main__":
    if "--hotels" in sys.argv:
        seed_places(PROCESSED_DIR / "hotels.json", "Accommodations")
    elif "--attractions" in sys.argv:
        seed_places(PROCESSED_DIR / "attractions.json", "Tourist Attractions")
    else:
        # Default: seed master file if exists, else attractions
        master = PROCESSED_DIR / "places_master.json"
        if master.exists():
            seed_places(master, "Master Knowledge Base")
        else:
            seed_places(PROCESSED_DIR / "attractions.json", "Tourist Attractions")
