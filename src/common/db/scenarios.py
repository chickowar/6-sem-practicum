import psycopg2
from common.config import POSTGRES_SCENARIOS_SETTINGS

def get_db_connection():
    return psycopg2.connect(**POSTGRES_SCENARIOS_SETTINGS)

def init_db():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    scenario_id UUID PRIMARY KEY,
                    video_path TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
    conn.close()