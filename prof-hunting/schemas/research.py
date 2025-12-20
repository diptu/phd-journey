from typing import Optional, List
from pydantic import BaseModel


class ResearchPaper(BaseModel):
    title: str
    authors: str  # required in DB, so make mandatory
    venue: Optional[str] = None
    year: Optional[int] = None
    focus_area: Optional[str] = None
    paper_link: Optional[str] = None
    abstract: Optional[str] = None
    university: Optional[str] = None
    impact_score: Optional[float] = None  # nullable in DB
    interest_keywords: Optional[str] = None

    # Review-related fields
    is_reviewed: Optional[bool] = False
    review_feedback: Optional[str] = "NOT_READ"
    review_notes: Optional[str] = None
    faculty_id: Optional[int] = None


class ResearchRegistryResponse(BaseModel):
    papers: List[ResearchPaper]
