import json
from common.db.scenarios import get_db_connection
from common.kafka.producer import get_producer, shutdown_producer
from common.config import KAFKA_RUNNER_COMMANDS_TOPIC
from orchestrator.commands import runner_command_queue


async def produce_runner_commands():
    producer = await get_producer()
    conn = await get_db_connection()
    try:
        while True:
            command = await runner_command_queue.get()
            scenario_id = command["scenario_id"]
            command_type = command.get("command", "start")

            message = {
                "scenario_id": scenario_id,
                "command": command_type
            }

            if command_type == "start":
                message["video_path"] = command["video_path"]
                message["start_frame"] = command.get("start_frame", 0)

                await conn.execute("""
                    UPDATE scenarios SET status = $1 WHERE scenario_id = $2
                """, "in_startup_processing", scenario_id)

                await producer.send_and_wait(
                    KAFKA_RUNNER_COMMANDS_TOPIC,
                    json.dumps(message).encode("utf-8"),
                    key=scenario_id.encode("utf-8")
                )

                print(f"[Orchestrator] Sent start command to runner for scenario {scenario_id}")

            elif command_type == "stop":
                await conn.execute("""
                    UPDATE scenarios SET status = $1 WHERE scenario_id = $2
                """, "in_shutdown_processing", scenario_id)

                # metadata = await producer.client.fetch_all_metadata()
                #
                # if KAFKA_RUNNER_COMMANDS_TOPIC not in metadata.topics:
                #     print(f"[ERROR] Topic {KAFKA_RUNNER_COMMANDS_TOPIC} not found in metadata")
                #     runner_command_queue.task_done()
                #     continue
                #
                # topic_metadata = metadata.topics[KAFKA_RUNNER_COMMANDS_TOPIC]
                # topic_partitions = list(topic_metadata.partitions.keys())
                # print(metadata, metadata.__dir__())
                #
                # for partition in topic_partitions:
                #     await producer.send_and_wait(
                #         KAFKA_RUNNER_COMMANDS_TOPIC,
                #         json.dumps(message).encode("utf-8"),
                #         partition=partition
                #     )

                await producer.send_and_wait(
                    KAFKA_RUNNER_COMMANDS_TOPIC,
                    json.dumps(message).encode("utf-8"),
                    key=scenario_id.encode("utf-8")
                )

                print(f"[Orchestrator] Sent stop command to ALL partitions for scenario {scenario_id}")

            runner_command_queue.task_done()

    finally:
        await shutdown_producer()
        await conn.close()
