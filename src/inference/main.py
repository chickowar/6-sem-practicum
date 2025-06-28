import asyncio
import json
import os

from common.kafka.consumer import get_consumer
from common.kafka.producer import get_producer, shutdown_producer
from common.config import KAFKA_FRAMES_TOPIC, KAFKA_PREDICTIONS_TOPIC
from inference.mock_inference import predict_frame_from_bytes

INFERENCE_ID = os.getenv("INFERENCE_ID", "inference-1")

print(1)

async def handle_frame_message(data: dict):
    scenario_id = data["scenario_id"]
    frame_number = data["frame_number"]
    frame_bytes_hex = data["frame_bytes"]
    frame_bytes = bytes.fromhex(frame_bytes_hex)

    print(f"[{INFERENCE_ID}] Received frame {frame_number} (scenario {scenario_id})")

    predictions = await predict_frame_from_bytes(frame_bytes)

    message = {
        "inference_id": INFERENCE_ID,
        "scenario_id": scenario_id,
        "frame_number": frame_number,
        "predictions": predictions,
    }

    producer = await get_producer()
    await producer.send_and_wait(
        KAFKA_PREDICTIONS_TOPIC,
        json.dumps(message).encode("utf-8"),
        key=scenario_id.encode("utf-8")
    )

    print(f"[{INFERENCE_ID}] Sent predictions for frame {frame_number} (scenario {scenario_id})")


async def consume_loop():
    consumer = await get_consumer(KAFKA_FRAMES_TOPIC, group_id="inference-group")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            await handle_frame_message(data)
    finally:
        await consumer.stop()


async def main():
    try:
        await consume_loop()
    finally:
        await shutdown_producer()


if __name__ == "__main__":
    asyncio.run(main())
