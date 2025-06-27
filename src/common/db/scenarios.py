import asyncio
import asyncpg
from common.config import POSTGRES_SCENARIOS_SETTINGS

async def get_db_connection():
    return await asyncpg.connect(**POSTGRES_SCENARIOS_SETTINGS)

async def init_db():
    conn = await get_db_connection()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            scenario_id UUID PRIMARY KEY,
            video_path TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    await conn.close()
    print('scenarios table made')

if __name__ == '__main__':
    asyncio.run(init_db())
