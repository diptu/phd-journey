from pydantic import BaseModel, Field, EmailStr, confloat
from typing import List, Optional


class FacultyMember(BaseModel):
    university: str
    department: str
    professor_name: str
    academic_tier: str
    research_focus: str
    future_job_prospect: str
    profile_link: Optional[str]
    email: str

    research_quality_rating: confloat(ge=0, le=10)
    funding_focus_rating: confloat(ge=0, le=10)

    lab_members_page: Optional[str]
    top_venues: str
    public_metrics: Optional[str]
    best_ta_ra_profile: Optional[str]
    best_paper: str


class FacultyRegistryResponse(BaseModel):
    faculty: List[FacultyMember]
