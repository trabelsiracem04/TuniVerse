# 🏛️ TuniVerse — System Design

---

## 1. High-Level Architecture

```mermaid
flowchart TD
    subgraph Client["🖥️ Client (Browser)"]
        UI["React SPA\nVite + TypeScript\nTailwind + shadcn/ui"]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        API["REST API\n/api/v1/..."]
        AUTH["JWT Auth\nMiddleware"]
        RAG["RAG Pipeline\nLlamaIndex / LangChain"]
        ITIN["Itinerary\nGenerator"]
        SSE["SSE Streaming\nEndpoint"]
    end

    subgraph DB["🗄️ Database (PostgreSQL)"]
        PG["Relational Tables\nusers · places · itineraries\nconversations · bookmarks"]
        VEC["pgvector\nplace embeddings"]
    end

    subgraph AI["🤖 AI Layer"]
        LLM["LLM\nOpenAI / Gemini / Mistral"]
        EMB["Embedding Model\ntext-embedding-3-small"]
    end

    subgraph External["🌐 External APIs"]
        MAP["OpenStreetMap\n(free, no key)"]
        WEATHER["OpenWeatherMap API"]
        FX["ExchangeRate API"]
    end

    UI -->|HTTP requests| API
    UI -->|SSE stream| SSE
    UI -->|map tiles| MAP
    API --> AUTH
    API --> RAG
    API --> ITIN
    RAG --> VEC
    RAG --> LLM
    ITIN --> LLM
    SSE --> RAG
    API --> PG
    EMB --> VEC
    UI --> WEATHER
    UI --> FX
```

---

## 2. Architecture Style

| Decision | Choice | Why |
|---|---|---|
| **Pattern** | Monolith (MVP) | Simpler to build, deploy, debug — split into services in v2 |
| **API style** | REST + SSE | REST for CRUD, SSE for streaming chat responses |
| **Auth** | Stateless JWT | No server-side session storage needed |
| **Vector store** | pgvector (in Postgres) | Avoids a separate vector DB (Pinecone/Weaviate) for MVP |
| **Streaming** | SSE (Server-Sent Events) | Simpler than WebSockets for one-way LLM token streaming |
| **Frontend** | SPA (Single Page App) | Fast navigation, map stays alive between route changes |

---

## 3. Component Breakdown

### 3.1 Frontend

```mermaid
flowchart LR
    subgraph Pages
        P1["/home\nLanding"]
        P2["/explore\nExplore + Filter + Map + Chat"]
        P3["/place/:id\nPlace Detail"]
        P4["/planner\nTrip Planner Form"]
        P5["/itinerary/:id\nItinerary View"]
        P6["/dashboard\nUser Profile"]
        P7["/admin\nAdmin Panel"]
    end

    subgraph Shared Components
        C1["FilterBar"]
        C2["PlaceCard"]
        C3["LeafletMap"]
        C4["AIChatPanel"]
        C5["ItineraryTimeline"]
        C6["Navbar / AuthGuard"]
    end

    subgraph State & Data
        S1["React Query\nServer state + caching"]
        S2["React Context\nAuth state"]
        S3["useStreamingChat\nSSE hook"]
    end
```

**Key frontend design decisions:**
- **React Query** handles all API calls, caching, and re-fetching — no manual `useEffect` for data fetching
- **React Router v6** with protected routes (AuthGuard wraps `/dashboard`, `/admin`)
- **Filter state lives in the URL** (`/explore?category=beach&city=Sousse`) — shareable links, back-button works
- **Map and chat panel share state** — highlighted place IDs flow through React Context

---

### 3.2 Backend Layer Structure

```
backend/app/
│
├── api/v1/              ← Route handlers (thin layer — no business logic)
│   ├── places.py        GET /places, GET /places/:id, GET /places/:id/similar
│   ├── chat.py          POST /chat/stream  (SSE)
│   ├── itineraries.py   POST /itineraries, GET /itineraries/:id
│   ├── auth.py          POST /auth/register, POST /auth/login
│   ├── bookmarks.py     POST/DELETE /bookmarks
│   └── admin.py         CRUD /admin/places
│
├── services/            ← Business logic
│   ├── place_service.py     filter, fetch, score recomputation
│   ├── chat_service.py      RAG retrieval + LLM call
│   ├── itinerary_service.py itinerary generation via LLM
│   └── auth_service.py      JWT creation, password hashing
│
├── rag/                 ← RAG pipeline
│   ├── embedder.py      text → vector (embedding model)
│   ├── retriever.py     vector similarity search against pgvector
│   └── pipeline.py      query → retrieve → prompt → stream
│
├── models/              ← SQLAlchemy ORM models
├── schemas/             ← Pydantic request/response schemas
├── core/                ← config, security, dependencies
└── db/                  ← session, base, seed
```

---

## 4. Data Flows

### 4.1 Explore & Filter Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React (Explore Page)
    participant API as FastAPI /places
    participant DB as PostgreSQL

    User->>UI: Selects filter (category=beach, city=Sousse)
    UI->>UI: Updates URL params
    UI->>API: GET /api/v1/places?category=beach&city=Sousse
    API->>DB: SELECT * FROM places WHERE category=beach AND city=Sousse ORDER BY recommendation_score DESC
    DB-->>API: Rows
    API-->>UI: JSON {total, places[]}
    UI->>UI: Renders PlaceCards (left panel)
    UI->>UI: Renders Leaflet markers (right map)
```

---

### 4.2 RAG Chatbot Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React (AIChatPanel)
    participant API as FastAPI /chat/stream
    participant RAG as RAG Pipeline
    participant VEC as pgvector
    participant LLM as LLM API

    User->>UI: Types "Best roman site near Tunis?"
    UI->>API: POST /chat/stream {message, conversation_id}
    API->>RAG: run_pipeline(query)
    RAG->>RAG: embed(query) → query_vector
    RAG->>VEC: SELECT places ORDER BY embedding <=> query_vector LIMIT 5
    VEC-->>RAG: Top-5 relevant places (context)
    RAG->>RAG: Build prompt (system + context + user query)
    RAG->>LLM: stream_completion(prompt)
    LLM-->>API: Token stream
    API-->>UI: SSE events (data: token\n\n)
    UI->>UI: Appends tokens to chat bubble live
    API->>DB: Save user message + assistant reply
```

---

### 4.3 Recommendation Score Update Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React
    participant API as GET /places/:id
    participant SVC as place_service
    participant DB as PostgreSQL

    User->>UI: Clicks on a PlaceCard
    UI->>API: GET /api/v1/places/42
    API->>SVC: get_place_by_id(42)
    SVC->>DB: UPDATE places SET view_count = view_count + 1 WHERE id = 42
    SVC->>DB: SELECT MAX(view_count) FROM places
    SVC->>DB: UPDATE all recommendation_scores\n= 0.6×(rate/5) + 0.4×(view_count/max)
    DB-->>SVC: Done
    SVC-->>API: Place object
    API-->>UI: JSON (full place detail)
    UI->>UI: Navigate to /place/42
```

---

## 5. RAG Pipeline — Deep Dive

```mermaid
flowchart TD
    A["User query\n'Best beach near Djerba'"] --> B["Embed query\ntext-embedding-3-small"]
    B --> C["Query vector\n1536 dimensions"]
    C --> D["pgvector search\nSELECT ... ORDER BY embedding <=> $1 LIMIT 5"]
    D --> E["Top-5 places\n(name, description, city, cost...)"]
    E --> F["Build prompt"]
    F --> G["LLM call\nstream tokens"]
    G --> H["SSE stream\nto frontend"]

    subgraph Prompt Structure
        F --> F1["SYSTEM: You are TuniVerse AI...\nOnly answer using the context below.\nIf unsure, say so."]
        F --> F2["CONTEXT:\n1. Djerba Island — sandy beach...\n2. Zarzis Beach — family friendly...\n..."]
        F --> F3["USER: Best beach near Djerba?"]
    end
```

**Guardrails built into the system prompt:**
- Must only use retrieved context — no fabrication
- Must refuse off-topic queries (politics, non-Tunisia topics)
- Must cite place names from context
- Must answer in English (MVP)

---

## 6. API Design

### Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | — | Health check |
| `GET` | `/api/v1/places` | — | List + filter places |
| `GET` | `/api/v1/places/:id` | — | Place detail (increments view_count) |
| `GET` | `/api/v1/places/:id/similar` | — | Similar places (same category/city) |
| `POST` | `/api/v1/chat/stream` | Optional | SSE streaming RAG chat |
| `POST` | `/api/v1/auth/register` | — | Create user account |
| `POST` | `/api/v1/auth/login` | — | Returns JWT token |
| `GET` | `/api/v1/itineraries/:id` | — | Get itinerary |
| `POST` | `/api/v1/itineraries` | Optional | Generate + save itinerary |
| `GET` | `/api/v1/bookmarks` | ✅ JWT | Get user bookmarks |
| `POST` | `/api/v1/bookmarks` | ✅ JWT | Add bookmark |
| `DELETE` | `/api/v1/bookmarks/:place_id` | ✅ JWT | Remove bookmark |
| `GET` | `/api/v1/admin/places` | ✅ Admin | List all places (admin) |
| `POST` | `/api/v1/admin/places` | ✅ Admin | Add new place |
| `PUT` | `/api/v1/admin/places/:id` | ✅ Admin | Update place |
| `DELETE` | `/api/v1/admin/places/:id` | ✅ Admin | Delete place |

### Standard Response Format
```json
// Success — list
{ "total": 42, "places": [ {...}, {...} ] }

// Success — single
{ "id": 1, "name": "El Jem", "city": "El Jem", ... }

// Error
{ "detail": "Place not found" }
```

---

## 7. Security Design

| Concern | Solution |
|---|---|
| **Password storage** | bcrypt hash — plaintext never stored |
| **Authentication** | JWT Bearer token (expires in 24h) |
| **Authorization** | Role-based: `user` vs `admin` checked in dependencies |
| **Input validation** | Pydantic schemas reject malformed requests automatically |
| **SQL injection** | SQLAlchemy ORM — no raw string queries |
| **CORS** | Restricted to `localhost:5173` (dev) and Vercel domain (prod) |
| **Prompt injection** | System prompt guardrails + input length cap |
| **API key exposure** | LLM key stored in `.env`, never sent to frontend |

---

## 8. Sprint-by-Sprint Build Order

```mermaid
flowchart LR
    S1["Sprint 1\n🗄️ DB + Filter API\nPlaces model\nSeed data\nGET /places"] -->
    S2["Sprint 2\n🖥️ Explore Page\nFilterBar\nPlaceCards\nLeaflet Map"] -->
    S3["Sprint 3\n🤖 RAG Pipeline\npgvector embeddings\nSSE /chat/stream\nChat Panel UI"] -->
    S4["Sprint 4\n🔐 Auth + Saving\nJWT login\nBookmarks\nItinerary gen"] -->
    S5["Sprint 5\n🚀 Polish + Deploy\nPlace Detail Page\nSimilar places\nVercel + Render"]
```

---

## 9. What is NOT in the System (MVP Scope)

| Excluded | Reason |
|---|---|
| Redis / caching layer | Not needed at this scale |
| Message queue (Celery, RQ) | No async background jobs needed in MVP |
| WebSockets | SSE is sufficient for one-way LLM streaming |
| Docker | MVP runs locally |
| FR / AR multilingual | Deferred to v2 |
| Payment / booking | Out of scope entirely |
| Native mobile app | Web-only |
| Separate vector DB (Pinecone) | pgvector handles it at MVP scale |
