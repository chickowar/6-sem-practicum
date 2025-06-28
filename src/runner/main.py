import asyncio
import json
import os
import time
from typing import Dict

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
MAX_FRAMES = 15

# Сценарии в работе: scenario_id -> {"task": asyncio.Task, "frame_number": int, "last_predicted_frame": int}
active_scenarios: Dict[str, Dict] = {}


async def run_scenario(scenario_id: str, video_path: str, start_frame: int = 0):
    """Задача отправки кадров по сценарию"""
    print(f"[{RUNNER_ID}] Starting scenario {scenario_id}")
    producer = await get_producer()
    frame_number = start_frame

    try:
        while frame_number < MAX_FRAMES:
            await asyncio.sleep(1)  # имитация задержки
            frame_bytes = b"mock_frame_bytes"

            message = {
                "scenario_id": scenario_id,
                "frame_number": frame_number,
                "frame_bytes": frame_bytes.hex()
            }

            await producer.send_and_wait(
                KAFKA_FRAMES_TOPIC,
                json.dumps(message).encode("utf-8"),
                key=scenario_id.encode("utf-8")
            )

            active_scenarios[scenario_id]["frame_number"] = frame_number
            print(f"[{RUNNER_ID}] Sent frame {frame_number} for scenario {scenario_id}")
            frame_number += 1

        print(f"[{RUNNER_ID}] Finished sending all frames for scenario {scenario_id}")
    except asyncio.CancelledError:
        print(f"[{RUNNER_ID}] Scenario {scenario_id} cancelled (frame loop)")
        raise


async def heartbeat_loop():
    """Фоновая задача отправки heartbeat'ов каждые 5 секунд"""
    producer = await get_producer()
    while True:
        await asyncio.sleep(5)
        tasks = []
        for scenario_id, info in active_scenarios.items():
            frame_number = info["last_predicted_frame"]
            heartbeat = {
                "runner_id": RUNNER_ID,
                "scenario_id": scenario_id,
                "frame_number": frame_number,
                "timestamp": time.time()
            }
            task = producer.send_and_wait(
                KAFKA_HEARTBEAT_TOPIC,
                json.dumps(heartbeat).encode("utf-8")
            )
            tasks.append(task)
            print(f"[{RUNNER_ID}] Heartbeat | Scenario {scenario_id} | Frame {frame_number} from {RUNNER_ID}")

        if tasks:
            await asyncio.gather(*tasks)


async def predictions_consumer_loop():
    """Фоновая задача: чтение предсказаний и запись в БД"""
    consumer = await get_consumer(KAFKA_PREDICTIONS_TOPIC, group_id=f"runner-{RUNNER_ID}")
    conn = await get_db_connection()
    producer = await get_producer()

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            frame_number = data["frame_number"]
            predictions = data["predictions"]

            await conn.execute("""
                INSERT INTO predictions (scenario_id, frame_number, predictions)
                VALUES ($1, $2, $3)
                ON CONFLICT (scenario_id, frame_number) DO UPDATE SET predictions = $3
            """, scenario_id, frame_number, json.dumps(predictions))

            print(f"[{RUNNER_ID}] Stored prediction for {scenario_id}, frame {frame_number}")

            if scenario_id in active_scenarios:
                active_scenarios[scenario_id]["last_predicted_frame"] = frame_number

            # Если это последний кадр — завершить сценарий
            if frame_number == MAX_FRAMES - 1 and scenario_id in active_scenarios:
                await producer.send_and_wait(
                    KAFKA_SCENARIO_EVENTS_TOPIC,
                    json.dumps({
                        "scenario_id": scenario_id,
                        "runner_id": RUNNER_ID,
                        "event": "scenario_completed",
                        "timestamp": time.time()
                    }).encode("utf-8")
                )
                print(f"[{RUNNER_ID}] Scenario {scenario_id} completed (all frames predicted)")

                task = active_scenarios[scenario_id]["task"]
                task.cancel()
                del active_scenarios[scenario_id]
    finally:
        await consumer.stop()
        await conn.close()


async def commands_consumer_loop():
    """Фоновая задача: получение команд запуска и остановки сценариев"""
    consumer = await get_consumer(KAFKA_RUNNER_COMMANDS_TOPIC, group_id="runner-group")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            scenario_id = data["scenario_id"]
            command = data.get("command", "start")

            if command == "start":
                if scenario_id in active_scenarios:
                    print(f"[{RUNNER_ID}] Scenario {scenario_id} already running")
                    continue

                task = asyncio.create_task(run_scenario(
                    scenario_id,
                    data.get("video_path", ""),
                    data.get("start_frame", 0)
                ))
                active_scenarios[scenario_id] = {
                    "task": task,
                    "frame_number": 0,
                    "last_predicted_frame": -1
                }

            elif command == "stop":
                if scenario_id in active_scenarios:
                    print(f"[{RUNNER_ID}] Stopping scenario {scenario_id}")
                    active_scenarios[scenario_id]["task"].cancel()
                    del active_scenarios[scenario_id]
                else:
                    print(f"[{RUNNER_ID}] Stop command received for unknown scenario {scenario_id}")
    finally:
        await consumer.stop()


async def main():
    try:
        await asyncio.gather(
            commands_consumer_loop(),
            predictions_consumer_loop(),
            heartbeat_loop(),
        )
    except asyncio.CancelledError:
        print(f"[{RUNNER_ID}] Runner shutdown triggered.")
    finally:
        await shutdown_producer()


if __name__ == "__main__":
    asyncio.run(main())
