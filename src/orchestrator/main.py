import asyncio
import json

from common.db.scenarios import get_db_connection
from common.kafka.consumer import get_consumer, shutdown_consumer
from common.kafka.producer import get_producer, shutdown_producer
from common.config import KAFKA_ORCHESTRATOR_COMMANDS_TOPIC, KAFKA_RUNNER_COMMANDS_TOPIC

runner_command_queue = asyncio.Queue()


async def consume_orchestrator_commands():
    consumer = await get_consumer(KAFKA_ORCHESTRATOR_COMMANDS_TOPIC, group_id="orchestrator-group")
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

            await runner_command_queue.put(msg.value)
    finally:
        await conn.close()
        await shutdown_consumer()


async def produce_runner_commands():
    producer = await get_producer()
    try:
        while True:
            msg = await runner_command_queue.get()
            await producer.send_and_wait(KAFKA_RUNNER_COMMANDS_TOPIC, msg)
            print(f"[Orchestrator] Sent command to runner: {msg}")
            runner_command_queue.task_done()
    finally:
        await shutdown_producer()


async def main():
    await asyncio.gather(
        consume_orchestrator_commands(),
        produce_runner_commands(),
    )

if __name__ == '__main__':
    asyncio.run(main())
