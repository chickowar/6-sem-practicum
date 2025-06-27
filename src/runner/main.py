import asyncio
import json
import random
from common.kafka.consumer import get_consumer, shutdown_consumer
from common.db.predictions import get_db_connection
from common.config import KAFKA_RUNNER_COMMANDS_TOPIC

MOCK = [
    {"class_id": 0, "label": "person"},
    {"class_id": 1, "label": "car"},
    {"class_id": 2, "label": "bicycle"}
]

async def mock_predict():
    rndchoice = random.choice(MOCK)
    return {
        "class_id": rndchoice["class_id"],
        "confidence": round(random.uniform(0.5, 0.99), 2),
        "bbox": [
            round(random.uniform(0, 100), 1),
            round(random.uniform(0, 100), 1),
            round(random.uniform(100, 200), 1),
            round(random.uniform(100, 300), 1),
        ],
        "label": rndchoice["label"]
    }

async def handle_scenario(data: dict):
    scenario_id = data["scenario_id"]
    video_path = data["video_path"]

    print(f"Runner started scenario {scenario_id} (video: {video_path})")

    conn = await get_db_connection()

    try:
        for frame_number in range(10):  # only 10 frames per vid
            await asyncio.sleep(2)  # mock of inference

            mock_result = [await mock_predict()]

            await conn.execute("""
                INSERT INTO predictions (scenario_id, frame_number, predictions)
                VALUES ($1, $2, $3)
                ON CONFLICT (scenario_id, frame_number) DO UPDATE SET predictions = $3
            """, scenario_id, frame_number, json.dumps(mock_result))

            print(f"  Frame {frame_number} written for scenario {scenario_id}")
    finally:
        await conn.close()

async def run():
    consumer = await get_consumer(KAFKA_RUNNER_COMMANDS_TOPIC, group_id="runner-group")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            print(f"DATA TYPE : ", type(data))
            await handle_scenario(data)
    finally:
        await shutdown_consumer()

asyncio.run(run())
