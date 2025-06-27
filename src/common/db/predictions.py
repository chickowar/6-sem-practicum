import asyncio
import asyncpg
from common.config import POSTGRES_PREDICTIONS_SETTINGS

async def get_db_connection():
    return await asyncpg.connect(**POSTGRES_PREDICTIONS_SETTINGS)

async def init_db():
    conn = await get_db_connection()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            scenario_id UUID NOT NULL,
            frame_number INTEGER NOT NULL,
            predictions JSONB NOT NULL,
            PRIMARY KEY (scenario_id, frame_number)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_scenario ON predictions(scenario_id);")
    await conn.close()
    print("predictions table made")

if __name__ == '__main__':
    asyncio.run(init_db())
