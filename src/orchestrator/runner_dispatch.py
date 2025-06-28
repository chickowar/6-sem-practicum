import json
from common.db.scenarios import get_db_connection
from common.kafka.producer import get_producer, shutdown_producer
from common.config import KAFKA_RUNNER_COMMANDS_TOPIC
from orchestrator.commands import runner_command_queue

async def produce_runner_commands():
    producer = await get_producer()
    # print(f'AWAITED PRODUCER in produce_runner_commands: {producer}')
    conn = await get_db_connection()
    try:
        while True:
            task = await runner_command_queue.get()
            scenario_id = task["scenario_id"]

            await producer.send_and_wait(KAFKA_RUNNER_COMMANDS_TOPIC, json.dumps(task).encode("utf-8"))
            print(f"[Orchestrator] Sent command to runner: {task}")

            await conn.execute("""
                UPDATE scenarios SET status = $1 WHERE scenario_id = $2
            """, "in_startup_processing", scenario_id)

            runner_command_queue.task_done()
    finally:
        await shutdown_producer()
        await conn.close()
