from aiokafka import AIOKafkaProducer
from common.config import KAFKA_BOOTSTRAP_SERVERS

_kafka_producer: AIOKafkaProducer | None = None

async def get_producer() -> AIOKafkaProducer:
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await _kafka_producer.start()
    return _kafka_producer

async def shutdown_producer():
    global _kafka_producer
    if _kafka_producer is not None:
        await _kafka_producer.stop()
        _kafka_producer = None
