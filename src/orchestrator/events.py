import json
from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer
from common.config import KAFKA_SCENARIO_EVENTS_TOPIC

async def consume_scenario_events():
    consumer = await get_consumer(KAFKA_SCENARIO_EVENTS_TOPIC, group_id="orchestrator-events-group")
    conn = await get_db_connection()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            event = data["event"]

            if event == "scenario_completed":
                await conn.execute("""
                    UPDATE scenarios SET status = $1 WHERE scenario_id = $2
                """, "inactive", scenario_id)

                print(f"[FSM] Scenario {scenario_id} -> inactive (completed by {data['runner_id']})")

    finally:
        await consumer.stop()
        await conn.close()
