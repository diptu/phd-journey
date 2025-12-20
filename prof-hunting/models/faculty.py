from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Index
from .base import Base


class FacultyRegistryDB(Base):
    __tablename__ = "faculty_registry"

    __table_args__ = (
        UniqueConstraint(
            "university",
            "department",
            "professor_name",
            name="uq_faculty_university_department_professor",
        ),
        Index(
            "ix_faculty_university_department",
            "university",
            "department",
            "professor_name",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    university = Column(String, nullable=False)
    department = Column(String, nullable=False)
    professor_name = Column(String, nullable=False)
    academic_tier = Column(String, nullable=False)
    research_focus = Column(String, nullable=False)
    future_job_prospect = Column(String, nullable=False)
    profile_link = Column(String)
    email = Column(String)
    research_quality_rating = Column(Float, nullable=False)
    funding_focus_rating = Column(Float, nullable=False)
    lab_members_page = Column(String)
    top_venues = Column(String, nullable=False)
    public_metrics = Column(String)
    best_ta_ra_profile = Column(String)
    best_paper = Column(String, nullable=False)
