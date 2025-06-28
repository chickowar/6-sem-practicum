import json
from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer
from common.config import KAFKA_SCENARIO_EVENTS_TOPIC
from orchestrator.heartbeats import last_heartbeat


async def consume_scenario_events():
    consumer = await get_consumer(KAFKA_SCENARIO_EVENTS_TOPIC, group_id="orchestrator-events-group")
    conn = await get_db_connection()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            event = data["event"]

            if event == "scenario_completed" or event == "scenario_cancelled":
                await conn.execute("""
                                   UPDATE scenarios
                                   SET status = $1
                                   WHERE scenario_id = $2
                                   """, "inactive" if event == "scenario_cancelled" else "scenario_completed", scenario_id)

                print(
                    f"[FSM] Scenario {scenario_id} -> {'inactive' if event == 'scenario_cancelled' else 'scenario_completed'} "
                    f"({event} by {data['runner_id']})")
                last_heartbeat.pop(str(scenario_id))
                print(f"[FSM] Deleted {scenario_id} heartbeat")


    finally:
        await consumer.stop()
        await conn.close()
