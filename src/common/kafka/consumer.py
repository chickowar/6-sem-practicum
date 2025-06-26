from aiokafka import AIOKafkaConsumer
from common.config import KAFKA_BOOTSTRAP_SERVERS

_kafka_consumer: AIOKafkaConsumer | None = None

async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    global _kafka_consumer
    if _kafka_consumer is None:
        _kafka_consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset="earliest"
        )
        await _kafka_consumer.start()
    return _kafka_consumer

async def shutdown_consumer():
    global _kafka_consumer
    if _kafka_consumer is not None:
        await _kafka_consumer.stop()
        _kafka_consumer = None
