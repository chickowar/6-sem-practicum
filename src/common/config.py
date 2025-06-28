import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")

KAFKA_ORCHESTRATOR_COMMANDS_TOPIC = "orchestrator_commands"
KAFKA_RUNNER_COMMANDS_TOPIC = "runner_commands"
KAFKA_HEARTBEAT_TOPIC = "heartbeat"
KAFKA_SCENARIO_EVENTS_TOPIC = "scenario_events"
KAFKA_FRAMES_TOPIC = "frames"
KAFKA_PREDICTIONS_TOPIC = "predictions"

POSTGRES_SCENARIOS_HOST = os.getenv("POSTGRES_SCENARIOS_HOST", "localhost")
POSTGRES_PREDICTIONS_HOST = os.getenv("POSTGRES_PREDICTIONS_HOST", "localhost")
POSTGRES_SCENARIOS_PORT = os.getenv("POSTGRES_SCENARIOS_PORT", "5432")
POSTGRES_PREDICTIONS_PORT = os.getenv("POSTGRES_PREDICTIONS_PORT", "5433")

POSTGRES_SCENARIOS_SETTINGS = {
    "host": POSTGRES_SCENARIOS_HOST,
    "port": POSTGRES_SCENARIOS_PORT,
    "database": "scenarios",
    "user": "postgres",
    "password": "mysecretpassword"
}

POSTGRES_PREDICTIONS_SETTINGS = {
    "host": POSTGRES_PREDICTIONS_HOST,
    "port": POSTGRES_PREDICTIONS_PORT,
    "database": "predictions",
    "user": "postgres",
    "password": "mysecretpassword"
}
