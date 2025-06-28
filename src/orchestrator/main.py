import asyncio
from orchestrator.commands import consume_orchestrator_commands
from orchestrator.events import consume_scenario_events
from orchestrator.runner_dispatch import produce_runner_commands
from orchestrator.heartbeats import consume_heartbeats
from orchestrator.monitor import heartbeat_monitor


async def main():
    await asyncio.gather(
        consume_orchestrator_commands(),
        consume_scenario_events(),
        consume_heartbeats(),
        heartbeat_monitor(),
        produce_runner_commands(),
    )

if __name__ == "__main__":
    asyncio.run(main())
