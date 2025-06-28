import asyncio
import json
from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer
from common.config import KAFKA_ORCHESTRATOR_COMMANDS_TOPIC

runner_command_queue = asyncio.Queue()

async def consume_orchestrator_commands():
    consumer = await get_consumer(KAFKA_ORCHESTRATOR_COMMANDS_TOPIC, group_id="orchestrator-group")
    # print(f'AWAITED CONSUMER in consume_orchestrator_commands: {consumer}')
    conn = await get_db_connection()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            print(f"[Orchestrator] Received scenario: {data}")

            await conn.execute("""
                INSERT INTO scenarios (scenario_id, video_path, status)
                VALUES ($1, $2, $3)
                ON CONFLICT (scenario_id) DO NOTHING
            """, data["scenario_id"], data["video_path"], "init_startup")

            await runner_command_queue.put({
                "scenario_id": data["scenario_id"],
                "video_path": data["video_path"],
                "start_frame": 0
            })
    finally:
        await conn.close()
        await consumer.stop()
