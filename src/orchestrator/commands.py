import asyncio
import json
from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer
from common.config import KAFKA_ORCHESTRATOR_COMMANDS_TOPIC
from orchestrator.heartbeats import last_heartbeat

runner_command_queue = asyncio.Queue()

async def consume_orchestrator_commands():
    consumer = await get_consumer(KAFKA_ORCHESTRATOR_COMMANDS_TOPIC, group_id="orchestrator-group")
    conn = await get_db_connection()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            status = data["status"]

            print(f"[Orchestrator] Received scenario command: {data}")

            if status == "init_startup":
                await conn.execute("""
                    INSERT INTO scenarios (scenario_id, video_path, status)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (scenario_id) DO NOTHING
                """, scenario_id, data["video_path"], status)

                await runner_command_queue.put({
                    "scenario_id": scenario_id,
                    "video_path": data["video_path"],
                    "start_frame": 0,
                    "command": "start"
                })

            elif status == "init_shutdown":
                await conn.execute("""
                    UPDATE scenarios
                    SET status = $1
                    WHERE scenario_id = $2
                """, status, scenario_id)

                print(f"[FSM] Scenario {scenario_id} -> init_shutdown")

                del last_heartbeat[str(scenario_id)]

                print(f"[FSM] Deleted {scenario_id} heartbeat")

                await runner_command_queue.put({
                    "scenario_id": scenario_id,
                    "command": "stop"
                })

    finally:
        await conn.close()
        await consumer.stop()
