# Routes
from fastapi import APIRouter, HTTPException

from common.db.scenarios import get_db_connection as get_scenarios_db_connection
from common.kafka.producer import get_producer
from common.config import KAFKA_ORCHESTRATOR_COMMANDS_TOPIC
import uuid, json

from videoanalysis.schemas import ScenarioCreateRequest, ScenarioCreateResponse, ScenarioResponse

router = APIRouter()


conn_scenarios = get_scenarios_db_connection()

@router.get("/scenario/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str) -> ScenarioResponse:
    with conn_scenarios:
        with conn_scenarios.cursor() as cur:
            cur.execute("SELECT video_path, status FROM scenarios WHERE scenario_id = %s",
                        (scenario_id,)
                        )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Scenario not found")
            return ScenarioResponse(**{"scenario_id": scenario_id, "video_path": row[0], "status": row[1]})

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