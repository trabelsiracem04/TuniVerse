# TuniVerse Data Pipeline & Tooling Scripts

Scripts for curating, formatting, seeding, and testing the TuniVerse knowledge base.

---

## 🛠️ Active Scripts & Tools

| Script | Purpose | Usage Command |
| :--- | :--- | :--- |
| **`enrich_place_descriptions.py`** | Scrapes French Wikipedia summaries and translates to English with academic quota rotation. | `python data/scripts/enrich_place_descriptions.py --start el-Mida` |
| **`enrich_place_images.py`** | Fixes place images, fetches authentic Wikimedia photos, and eliminates duplicate fallback pictures. | `python data/scripts/enrich_place_images.py` |
| **`format_places_dataset.py`** | Formats tourist places into the exact 16-field schema (IDs 118+, regions, AMVPPC tickets, ratings). | `python data/scripts/format_places_dataset.py` |
| **`seed_database.py`** | Universal seeder for Supabase PostgreSQL (seeds hotels, attractions, or complete master catalog). | `python data/scripts/seed_database.py` |
| **`test_recommendation.py`** | Tests recommendation score formula (60/40 quality vs popularity) & live database re-ranking. | `python data/scripts/test_recommendation.py` |
| **`test_db_connection.py`** | Verifies database connectivity to Supabase and checks active extensions. | `python data/scripts/test_db_connection.py` |

---

## 🧠 Recommendation Score Logic

Formula implemented in `backend/app/services/place_service.py` and tested by `test_recommendation.py`:

$$\text{recommendation\_score} = 0.6 \times \left(\frac{\text{rate}}{5.0}\right) + 0.4 \times \left(\frac{\text{view\_count}}{\text{max\_view\_count}}\right)$$

- **60% Quality Weight**: Normalized rating (`rate / 5.0`).
- **40% Popularity Weight**: Normalized views (`view_count / max_views`).
- **Performance**: Single atomic SQL batch query updating all places in `<10ms`.
- **Dynamic Re-ranking**: When a place detail is viewed (`GET /api/v1/places/{id}`), `view_count` increments and scores are re-computed automatically.

---

## 🚀 Execution Flow

1. **Step 1: Scrape & Enrich Descriptions**
   ```bash
   python data/scripts/enrich_place_descriptions.py --start el-Mida
   ```

2. **Step 2: Format to 16-field Target Schema**
   ```bash
   python data/scripts/format_places_dataset.py
   ```

3. **Step 3: Seed Database**
   ```bash
   python data/scripts/seed_hotels.py
   ```

4. **Step 4: Verify Recommendation Engine**
   ```bash
   python data/scripts/test_recommendation.py
   ```
