from pydantic import BaseModel

# POST /scenario/
class ScenarioCreateRequest(BaseModel):
    video_path: str
class ScenarioCreateResponse(BaseModel):
    scenario_id: str
    status: str

# GET /scenario/<scenario_id>
class ScenarioResponse(BaseModel):
    scenario_id: str
    video_path: str
    status: str