KAFKA_BOOTSTRAP_SERVERS = "localhost:29092" # ПРИ ЗАПУСКЕ С ДОКЕРА НУЖНО ДРУГОЕ!
KAFKA_ORCHESTRATOR_COMMANDS_TOPIC = "orchestrator_commands"
KAFKA_RUNNER_COMMANDS_TOPIC = "runner_commands"
KAFKA_HEARTBEAT_TOPIC = "heartbeat"

POSTGRES_SCENARIOS_SETTINGS = {
    "host": "localhost",
    "port": 5432,
    "database": "scenarios",
    "user": "postgres",
    "password": "mysecretpassword"
}

POSTGRES_PREDICTIONS_SETTINGS = {
    "host": "localhost",
    "port": 5433,
    "database": "predictions",
    "user": "postgres",
    "password": "mysecretpassword"
}
