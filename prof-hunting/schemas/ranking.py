from pydantic import BaseModel, Field, conint, confloat
from typing import List


class UniversityRanking(BaseModel):
    rank: conint(gt=0)
    institution: str
    state: str = Field(..., min_length=2, max_length=2)
    peer_assessment_score: confloat(ge=0, le=5)


class RankingsResponse(BaseModel):
    rankings: List[UniversityRanking]
