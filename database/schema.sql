-- =============================================================
--  TuniVerse — Database Schema
--  Engine  : PostgreSQL 15+
--  Ext.    : pgvector (added in Sprint 3 for RAG embeddings)
-- =============================================================

-- Enable pgvector extension (run once, requires superuser)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================
--  TABLE: users
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL          PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    name            VARCHAR(100)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'user'
                                    CHECK (role IN ('user', 'admin')),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);


-- =============================================================
--  TABLE: places
-- =============================================================
CREATE TABLE IF NOT EXISTS places (
    id                      SERIAL          PRIMARY KEY,
    name                    VARCHAR(200)    NOT NULL,
    city                    VARCHAR(100)    NOT NULL,
    region                  VARCHAR(100)    NOT NULL,
    category                VARCHAR(50)     NOT NULL,
    sub_category            VARCHAR(100),
    description             TEXT            NOT NULL,
    short_desc              VARCHAR(300)    NOT NULL,
    cover_image             VARCHAR(500),
    images                  TEXT[]          NOT NULL DEFAULT '{}',
    latitude                FLOAT           NOT NULL,
    longitude               FLOAT           NOT NULL,
    cost_estimate           VARCHAR(100),
    rate                    FLOAT           NOT NULL DEFAULT 0.0
                                            CHECK (rate >= 0.0 AND rate <= 5.0),
    view_count              INTEGER         NOT NULL DEFAULT 0,
    recommendation_score    FLOAT           NOT NULL DEFAULT 0.0,

    -- Sprint 3: uncomment once pgvector extension is enabled
    -- embedding            vector(1536),

    created_at              TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_places_city         ON places (city);
CREATE INDEX IF NOT EXISTS idx_places_category     ON places (category);
CREATE INDEX IF NOT EXISTS idx_places_sub_category ON places (sub_category);
CREATE INDEX IF NOT EXISTS idx_places_score        ON places (recommendation_score DESC);

-- Sprint 3: vector similarity index (IVFFlat, cosine distance)
-- CREATE INDEX IF NOT EXISTS idx_places_embedding
--     ON places USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- =============================================================
--  TABLE: itineraries
-- =============================================================
CREATE TABLE IF NOT EXISTS itineraries (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         REFERENCES users (id) ON DELETE SET NULL,
    title           VARCHAR(200)    NOT NULL,
    region          VARCHAR(100)    NOT NULL,
    duration_days   INTEGER         NOT NULL,
    budget_tier     VARCHAR(20)     NOT NULL DEFAULT 'mid'
                                    CHECK (budget_tier IN ('budget', 'mid', 'luxury')),
    num_travelers   INTEGER         NOT NULL DEFAULT 1,
    interest_tags   TEXT[]          NOT NULL DEFAULT '{}',
    notes           TEXT,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries (user_id);


-- =============================================================
--  TABLE: itinerary_places  (junction: itinerary <-> place)
-- =============================================================
CREATE TABLE IF NOT EXISTS itinerary_places (
    id              SERIAL          PRIMARY KEY,
    itinerary_id    INTEGER         NOT NULL
                                    REFERENCES itineraries (id) ON DELETE CASCADE,
    place_id        INTEGER         NOT NULL
                                    REFERENCES places (id) ON DELETE RESTRICT,
    day_number      INTEGER         NOT NULL,
    order_in_day    INTEGER         NOT NULL,
    tip             VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_itin_places_lookup
    ON itinerary_places (itinerary_id, day_number, order_in_day);


-- =============================================================
--  TABLE: conversations
-- =============================================================
CREATE TABLE IF NOT EXISTS conversations (
    id          SERIAL          PRIMARY KEY,
    user_id     INTEGER         REFERENCES users (id) ON DELETE SET NULL,
    title       VARCHAR(200),
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id);


-- =============================================================
--  TABLE: messages
-- =============================================================
CREATE TABLE IF NOT EXISTS messages (
    id                  SERIAL          PRIMARY KEY,
    conversation_id     INTEGER         NOT NULL
                                        REFERENCES conversations (id) ON DELETE CASCADE,
    role                VARCHAR(10)     NOT NULL
                                        CHECK (role IN ('user', 'assistant')),
    content             TEXT            NOT NULL,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id);


-- =============================================================
--  TABLE: bookmarks  (user <-> place, no duplicates)
-- =============================================================
CREATE TABLE IF NOT EXISTS bookmarks (
    user_id     INTEGER     NOT NULL REFERENCES users  (id) ON DELETE CASCADE,
    place_id    INTEGER     NOT NULL REFERENCES places (id) ON DELETE CASCADE,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, place_id)
);
