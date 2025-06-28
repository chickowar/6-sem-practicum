import asyncio
import time
from common.db.scenarios import get_db_connection
from orchestrator.commands import runner_command_queue
from orchestrator.heartbeats import last_heartbeat

HEARTBEAT_TIMEOUT = 10

async def heartbeat_monitor():
    conn = await get_db_connection()
    try:
        while True:
            await asyncio.sleep(5)
            now = time.time()

            rows = await conn.fetch("""
                SELECT scenario_id, status, video_path
                FROM scenarios
                WHERE status NOT IN ('completed', 'inactive', 'init_shutdown')
            """)

            for row in rows:
                scenario_id = row["scenario_id"]
                str_scenario_id = str(scenario_id)
                status = row["status"]
                video_path = row["video_path"]

                info = last_heartbeat.get(str_scenario_id)
                # print('[Monitor] info = {} | len(last_heartbeat) = {}'.format(info, len(last_heartbeat)))
                # print('[Monitor] scenario_id = {} | last_heartbeat = {}'.format(scenario_id, last_heartbeat))
                # if len(last_heartbeat) > 0:
                #     print('[Monitor] type(scenario_id) = {} | type(...last_heartbeat) {}'.format(type(scenario_id), type(next(iter(last_heartbeat))[0]) ))
                if info and (now - info["timestamp"] > HEARTBEAT_TIMEOUT):
                    print(f"[Monitor] Lost heartbeat for scenario {scenario_id}, rescheduling...")

                    await conn.execute("""
                        UPDATE scenarios SET status = $1 WHERE scenario_id = $2
                    """, "in_startup_processing", scenario_id)

                    await runner_command_queue.put({
                        "scenario_id": str_scenario_id,
                        "video_path": video_path,
                        "start_frame": info["frame_number"] + 1
                    })
                    del last_heartbeat[str_scenario_id]
    finally:
        await conn.close()
