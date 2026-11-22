import os
from dotenv import load_dotenv
import sqlalchemy

load_dotenv(r'd:\ALL_PROJECTS\TuniVerse\backend\.env')
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('DATABASE_URL not found in backend/.env')
    exit(0)

# Mask password for safe display
masked_url = re_sub = db_url.split('@')[-1] if '@' in db_url else 'configured'
print(f"Connecting to host: ...@{masked_url}")

try:
    engine = sqlalchemy.create_engine(db_url)
    with engine.connect() as conn:
        res = conn.execute(sqlalchemy.text('SELECT version();')).fetchone()
        print('✅ Connected to Supabase PostgreSQL successfully!')
        print('Postgres Version:', res[0][:50])

        vec = conn.execute(sqlalchemy.text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchone()
        if vec:
            print('✅ pgvector extension is ENABLED!')
        else:
            print('⚠️ pgvector extension is NOT enabled yet (you can run: CREATE EXTENSION vector; in Supabase SQL Editor)')
except Exception as e:
    print('❌ Connection error:', e)
