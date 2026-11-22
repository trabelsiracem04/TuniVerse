# 🌍 TuniVerse — AI-Powered Tourism Platform for Tunisia

> **Academic Project** — Dynamic Web Development (TP Développement Web Dynamique)  
> **Institution:** ENET'Com (École Nationale d'Électronique et des Télécommunications de Sfax)  
> **Class:** 2nd Year IDSD — Group 2IDSD2 (2026–2027)  
> **Team:** Ali Kchaou & Racem Trabelsi  

---

## 📖 About the Project

**TuniVerse** is a full-stack, intelligent web platform designed as a virtual travel assistant for Tunisia. It combines:
- 🏛️ **Explore Tunisia Directory:** Searchable and filterable catalog of attractions, monuments, hotels, and beaches with map visualizer.
- 🤖 **AI Assistant:** RAG-powered chatbot delivering verified, grounded advice without hallucinations.
- 🧭 **Recommendation System:** Ranks destinations dynamically based on popularity and ratings.
- 🗺️ **Interactive Leaflet Map:** Displays attraction pins synchronized with filtered cards.

> **Current Scope (MVP):**
> - Language: **English only** (multilingual FR/AR planned for v2)
> - Database: **Hosted on Supabase** (PostgreSQL 19 + pgvector)
> - Deployment: Local development without Docker for MVP simplicity

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React (Vite), TypeScript, Tailwind CSS, shadcn/ui, Leaflet |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **Database** | Supabase (Cloud PostgreSQL 19 + pgvector) |
| **AI / RAG** | LlamaIndex / LangChain (Sprint 3) |

---

## 🚀 Quick Start (Backend)

### 1. Prerequisites
- Python 3.12+ installed
- Access to the team Supabase database connection string

### 2. Environment Setup
Create a `.env` file in the root project folder (`TuniVerse/.env`):
```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-1-eu-north-1.pooler.supabase.com:5432/postgres
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```

### 3. Install Dependencies & Run
```powershell
# Navigate to backend
cd backend

# Install packages
pip install -r requirements.txt

# Start local server
uvicorn app.main:app --reload
```

* API Docs (Swagger UI): **`http://localhost:8000/docs`**
* Health Check: **`http://localhost:8000/health`**

---

## 📁 Project Architecture & Docs

All specifications and sprint plans are stored in the [`docs/`](./docs) folder:

- 📄 [`docs/TuniVerse_Overview.md`](./docs/TuniVerse_Overview.md) — Comprehensive project overview and specifications.
- 🗂️ [`docs/TuniVerse_Backlog.md`](./docs/TuniVerse_Backlog.md) — Product backlog with user stories, acceptance criteria, and story points.
- 🏛️ [`docs/System_Design.md`](./docs/System_Design.md) — System architecture, data flow diagrams, and endpoint specifications.
- 🗄️ [`docs/DB_Schema.md`](./docs/DB_Schema.md) — ER diagram and database table schemas.
- 🏃 [`docs/Sprint1_Plan.md`](./docs/Sprint1_Plan.md) — Sprint 1 step-by-step tasks and Definition of Done (✅ Completed).

---

## 📅 Sprint Progress

- [x] **Sprint 1 (Backend Foundation):** Place model, Supabase migration, filter API, placeholder recommendation system.
- [ ] **Sprint 2 (Frontend Core):** FilterBar, PlaceCards list, Leaflet map synchronization.
- [ ] **Sprint 3 (AI / RAG Pipeline):** In-page chatbot, vector embeddings with pgvector.
- [ ] **Sprint 4 (Auth & Itineraries):** JWT authentication, user bookmarks, itinerary generator.
- [ ] **Sprint 5 (Integration & Polish):** Place detail view, similar places, deployment.
