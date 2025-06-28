import json
from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer
from common.config import KAFKA_HEARTBEAT_TOPIC

last_heartbeat = {}  # scenario_id -> {timestamp, frame_number}

async def consume_heartbeats():
    consumer = await get_consumer(KAFKA_HEARTBEAT_TOPIC, group_id="orchestrator-heartbeat-group")
    # print(f'AWAITED CONSUMER in consume_heartbeats: {consumer}')
    conn = await get_db_connection()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            frame_number = data["frame_number"]
            timestamp = data["timestamp"]

            first = scenario_id not in last_heartbeat
            last_heartbeat[scenario_id] = {
                "timestamp": timestamp,
                "frame_number": frame_number
            }

            print(f"[Heartbeat] Scenario {scenario_id} | Frame {frame_number} from {data['runner_id']}")

            if first:
                await conn.execute("""
                    UPDATE scenarios SET status = $1 WHERE scenario_id = $2
                """, "active", scenario_id)
                print(f"[FSM] Scenario {scenario_id} -> active")
    finally:
        await conn.close()
        await consumer.stop()