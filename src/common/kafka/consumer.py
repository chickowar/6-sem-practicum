from aiokafka import AIOKafkaConsumer
from common.config import KAFKA_BOOTSTRAP_SERVERS

async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        auto_offset_reset="earliest"
    )
    await consumer.start()
    return consumer
