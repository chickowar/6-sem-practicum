import asyncio
import json
import os
import random
import time
from typing import Optional

from common.kafka.consumer import get_consumer
from common.kafka.producer import get_producer, shutdown_producer
from common.db.predictions import get_db_connection
from common.config import (
    KAFKA_RUNNER_COMMANDS_TOPIC,
    KAFKA_HEARTBEAT_TOPIC,
    KAFKA_SCENARIO_EVENTS_TOPIC,
)

MOCK = [
    {"class_id": 0, "label": "person"},
    {"class_id": 1, "label": "car"},
    {"class_id": 2, "label": "bicycle"}
]

RUNNER_ID = os.getenv("RUNNER_ID", "runner-1")

scenario_tasks: dict[str, asyncio.Task] = {}

frame_number_shared: Optional[int] = None


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


async def heartbeat_loop(scenario_id: str):
    global frame_number_shared
    producer = await get_producer()
    try:
        while True:
            await asyncio.sleep(5)
            if frame_number_shared is None:
                continue
            message = {
                "runner_id": RUNNER_ID,
                "scenario_id": scenario_id,
                "frame_number": frame_number_shared,
                "timestamp": time.time()
            }
            await producer.send_and_wait(KAFKA_HEARTBEAT_TOPIC, json.dumps(message).encode("utf-8"))
            print(f"[{RUNNER_ID}] Sent heartbeat: scenario={scenario_id}, frame={frame_number_shared}")
    except asyncio.CancelledError:
        print(f"[{RUNNER_ID}] Heartbeat loop cancelled for {scenario_id}")
        raise


async def handle_scenario_start(data: dict):
    global frame_number_shared

    scenario_id = data["scenario_id"]
    video_path = data["video_path"]
    start_frame = data.get("start_frame", 0)

    print(f"[{RUNNER_ID}] Started scenario {scenario_id} from frame {start_frame}")

    conn = await get_db_connection()
    heartbeat_task = asyncio.create_task(heartbeat_loop(scenario_id))

    try:
        for frame_number in range(start_frame, 15):  # 15 — мок, как будто конец видео
            await asyncio.sleep(3)
            mock_result = [await mock_predict()]

            await conn.execute("""
                INSERT INTO predictions (scenario_id, frame_number, predictions)
                VALUES ($1, $2, $3)
                ON CONFLICT (scenario_id, frame_number) DO UPDATE SET predictions = $3
            """, scenario_id, frame_number, json.dumps(mock_result))

            frame_number_shared = frame_number
            print(f"[{RUNNER_ID}] Frame {frame_number} written for scenario {scenario_id}")
        else:
            producer = await get_producer()
            end_message = {
                "scenario_id": scenario_id,
                "runner_id": RUNNER_ID,
                "event": "scenario_completed",
                "timestamp": time.time()
            }
            await producer.send_and_wait(KAFKA_SCENARIO_EVENTS_TOPIC, json.dumps(end_message).encode("utf-8"))
            print(f"[{RUNNER_ID}] Sent scenario_completed for {scenario_id}")

    except asyncio.CancelledError:
        print(f"[{RUNNER_ID}] Scenario {scenario_id} was cancelled")

        producer = await get_producer()
        cancel_message = {
            "scenario_id": scenario_id,
            "runner_id": RUNNER_ID,
            "event": "scenario_cancelled",
            "timestamp": time.time()
        }
        await producer.send_and_wait(KAFKA_SCENARIO_EVENTS_TOPIC, json.dumps(cancel_message).encode("utf-8"))

    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)
        await conn.close()
        print(f"[{RUNNER_ID}] Finished scenario {scenario_id}")


async def consume_loop():
    consumer = await get_consumer(KAFKA_RUNNER_COMMANDS_TOPIC, group_id="runner-group")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            command = data.get("command", "start")

            if command == "start":
                # запустить обработку
                if scenario_id in scenario_tasks:
                    print(f"[{RUNNER_ID}] Scenario {scenario_id} is already running")
                    continue
                task = asyncio.create_task(handle_scenario_start(data))
                scenario_tasks[scenario_id] = task

            elif command == "stop":
                task = scenario_tasks.get(scenario_id)
                if task:
                    task.cancel()
                    print(f"[{RUNNER_ID}] Stop command received for scenario {scenario_id}")
                else:
                    print(f"[{RUNNER_ID}] Stop command received, but no active task for scenario {scenario_id}") # вот такого не должно быть ваще в теории

    finally:
        await consumer.stop()


async def main():
    try:
        await consume_loop()
    finally:
        await shutdown_producer()


if __name__ == "__main__":
    asyncio.run(main())
