from pydantic import BaseModel
from typing import List, Dict, Any

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


# GET /prediction/<scenario_id>
class FramePrediction(BaseModel):
    frame_number: int
    predictions: List[Dict[str, Any]]