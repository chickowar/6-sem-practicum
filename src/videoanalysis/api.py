from fastapi import APIRouter, HTTPException
from common.db.scenarios import get_db_connection as get_scenarios_db_connection
from common.db.predictions import get_db_connection as get_predictions_db_connection
from common.kafka.producer import get_producer
from common.config import KAFKA_ORCHESTRATOR_COMMANDS_TOPIC
import uuid, json
from typing import List
from videoanalysis.schemas import (
    ScenarioCreateRequest,
    ScenarioCreateResponse,
    ScenarioResponse,
    FramePrediction
)

router = APIRouter()


@router.get("/scenario/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str) -> ScenarioResponse | None:
    conn = await get_scenarios_db_connection()
    try:
        row = await conn.fetchrow("SELECT video_path, status FROM scenarios WHERE scenario_id = $1", scenario_id)
        if not row:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return ScenarioResponse(
            scenario_id=scenario_id,
            video_path=row["video_path"],
            status=row["status"]
        )
    finally:
        await conn.close()


@router.get("/prediction/{scenario_id}", response_model=List[FramePrediction])
async def get_predictions(scenario_id: str) -> List[FramePrediction] | None:
    conn = await get_predictions_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT frame_number, predictions
            FROM predictions
            WHERE scenario_id = $1
            ORDER BY frame_number ASC
        """, scenario_id)

        return [
            FramePrediction(
                frame_number=row["frame_number"],
                predictions=json.loads(row["predictions"]) if isinstance(row["predictions"], str) else row[
                    "predictions"]
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.post("/scenario/", response_model=ScenarioCreateResponse)
async def create_scenario(req: ScenarioCreateRequest) -> ScenarioCreateResponse:
    scenario_id = str(uuid.uuid4())

    payload = json.dumps({
        "scenario_id": scenario_id,
        "video_path": req.video_path
    }).encode()

    producer = await get_producer()
    await producer.send_and_wait(KAFKA_ORCHESTRATOR_COMMANDS_TOPIC, payload)

    return ScenarioCreateResponse(
        scenario_id=scenario_id,
        status="pending"
    ) # стоит ли реально отсылать ending, если мы даже не знаем дошло ли до оркестратора????