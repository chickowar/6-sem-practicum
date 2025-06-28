import random
from typing import List
import asyncio

MOCK = [
    {"class_id": 0, "label": "person"},
    {"class_id": 1, "label": "car"},
    {"class_id": 2, "label": "bicycle"}
]

async def mock_predict():
    rndchoice = random.choice(MOCK)
    await asyncio.sleep(0.2)
    return {
        "class_id": rndchoice["class_id"],
        "confidence": round(random.uniform(0.5, 0.99), 2),
        "bbox": [
            round(random.uniform(0, 100), 1),
            round(random.uniform(0, 100), 1),
            round(random.uniform(100, 200), 1),
            round(random.uniform(100, 300), 1),
        ],
        "label": rndchoice["label"]
    }

async def predict_frame_from_bytes(frame_bytes: bytes) -> List[dict]:
    """
    **input**: jpeg bytes,
    \
    **output**: YOLO prediction
    """

    await asyncio.sleep(random.uniform(0.5, 3))

    return [
        await mock_predict() for i in range(random.randint(1, 6))
    ]

