import asyncio
import json
import os
import time
from typing import Optional, Dict, Tuple

from common.kafka.consumer import get_consumer
from common.kafka.producer import get_producer, shutdown_producer
from common.db.predictions import get_db_connection
from common.config import (
    KAFKA_RUNNER_COMMANDS_TOPIC,
    KAFKA_HEARTBEAT_TOPIC,
    KAFKA_SCENARIO_EVENTS_TOPIC,
    KAFKA_FRAMES_TOPIC,
    KAFKA_PREDICTIONS_TOPIC,
)

RUNNER_ID = os.getenv("RUNNER_ID", "runner-1")

scenario_tasks: dict[str, asyncio.Task] = {}
frame_number_shared: Dict[str, int] = {}
pending_predictions: Dict[Tuple[str, int], asyncio.Future] = {}


async def heartbeat_loop(scenario_id: str):
    producer = await get_producer()
    try:
        while True:
            await asyncio.sleep(5)
            frame_number = frame_number_shared.get(scenario_id)
            if frame_number is None:
                continue
            message = {
                "runner_id": RUNNER_ID,
                "scenario_id": scenario_id,
                "frame_number": frame_number,
                "timestamp": time.time()
            }
            await producer.send_and_wait(KAFKA_HEARTBEAT_TOPIC, json.dumps(message).encode("utf-8"))
            print(f"[{RUNNER_ID}] Sent heartbeat: scenario={scenario_id}, frame={frame_number}")
    except asyncio.CancelledError:
        print(f"[{RUNNER_ID}] Heartbeat loop cancelled for {scenario_id}")
        raise


async def send_frame(scenario_id: str, frame_number: int):
    producer = await get_producer()
    frame_bytes = b"fake_frame_bytes"  # Мок-байты, позже заменить
    frame_hex = frame_bytes.hex()

    message = {
        "scenario_id": scenario_id,
        "frame_number": frame_number,
        "frame_bytes": frame_hex
    }

    await producer.send_and_wait(
        KAFKA_FRAMES_TOPIC,
        json.dumps(message).encode("utf-8"),
        key=scenario_id.encode("utf-8")
    )

    print(f"[{RUNNER_ID}] Sent frame {frame_number} for scenario {scenario_id}")


async def handle_scenario_start(data: dict):
    global pending_predictions
    scenario_id = data["scenario_id"]
    video_path = data["video_path"]
    start_frame = data.get("start_frame", 0)

    print(f"[{RUNNER_ID}] Started scenario {scenario_id} from frame {start_frame}")

    conn = await get_db_connection()
    heartbeat_task = asyncio.create_task(heartbeat_loop(scenario_id))

    try:
        for frame_number in range(start_frame, 15):
            await asyncio.sleep(1)  # эмуляция задержки чтения кадра
            await send_frame(scenario_id, frame_number)

            loop = asyncio.get_event_loop()
            future = loop.create_future()
            pending_predictions[(scenario_id, frame_number)] = future

            predictions = await asyncio.wait_for(future, timeout=10)
            await conn.execute("""
                INSERT INTO predictions (scenario_id, frame_number, predictions)
                VALUES ($1, $2, $3)
                ON CONFLICT (scenario_id, frame_number) DO UPDATE SET predictions = $3
            """, scenario_id, frame_number, json.dumps(predictions))

            frame_number_shared[scenario_id] = frame_number
            print(f"[{RUNNER_ID}] Frame {frame_number} stored for scenario {scenario_id}")

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
        pending_predictions = {
            key: fut for key, fut in pending_predictions.items()
            if key[0] != scenario_id
        }
        frame_number_shared.pop(scenario_id, None)
        await conn.close()
        print(f"[{RUNNER_ID}] Finished scenario {scenario_id}")


async def listen_predictions():
    consumer = await get_consumer(KAFKA_PREDICTIONS_TOPIC, group_id=f"runner-{RUNNER_ID}")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            frame_number = data["frame_number"]
            predictions = data["predictions"]
            key = (scenario_id, frame_number)
            future = pending_predictions.get(key)
            if future and not future.done():
                future.set_result(predictions)
                print(f"[{RUNNER_ID}] Received predictions for scenario {scenario_id}, frame {frame_number}")
    finally:
        await consumer.stop()


async def consume_loop():
    consumer = await get_consumer(KAFKA_RUNNER_COMMANDS_TOPIC, group_id="runner-group")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            command = data.get("command", "start")

            if command == "start":
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
                    print(f"[{RUNNER_ID}] Stop command received, but no active task for scenario {scenario_id}")
    finally:
        await consumer.stop()


async def main():
    try:
        await asyncio.gather(
            consume_loop(),
            listen_predictions(),
        )
    finally:
        await shutdown_producer()


if __name__ == "__main__":
    asyncio.run(main())
