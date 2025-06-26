import asyncio, json
from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer, shutdown_consumer
from common.config import KAFKA_ORCHESTRATOR_COMMANDS_TOPIC

conn = get_db_connection()

async def consume():
    consumer = await get_consumer(KAFKA_ORCHESTRATOR_COMMANDS_TOPIC, group_id="orchestrator-group")

    async for msg in consumer:
        data = json.loads(msg.value.decode())
        print("Received:", data)
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scenarios (scenario_id, video_path, status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (scenario_id) DO NOTHING
                """, (data["scenario_id"], data["video_path"], "init_startup"))

    await shutdown_consumer()

asyncio.run(consume())
