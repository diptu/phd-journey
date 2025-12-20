from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from .base import Base
from .enums import ReviewFeedbackEnum


class ResearchRegistryDB(Base):
    __tablename__ = "research_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    authors = Column(String, nullable=False)  # just text for display
    venue = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    focus_area = Column(String, nullable=False)
    abstract = Column(Text)
    paper_link = Column(String, nullable=False)
    university = Column(String, nullable=True)

    impact_score = Column(Float)
    interest_keywords = Column(String, nullable=True)

    # Review tracking
    is_reviewed = Column(Boolean, default=False, nullable=False)
    review_feedback = Column(
        Enum(
            ReviewFeedbackEnum,
            name="review_feedback_enum",
            create_constraint=True,
            native_enum=True,
        ),
        default=ReviewFeedbackEnum.NOT_READ,
        nullable=False,
    )
    review_notes = Column(Text)

    # Link to Faculty by ID (robust)
    faculty_id = Column(
        Integer, ForeignKey("faculty_registry.id", ondelete="SET NULL"), nullable=True
    )
    faculty = relationship("FacultyRegistryDB", backref="papers")

    __table_args__ = (
        UniqueConstraint("title", "venue", "year", name="uq_paper_identity"),
        Index("ix_focus_area", "focus_area"),
        Index("ix_review_status", "is_reviewed"),
        Index("ix_venue_year", "venue", "year"),
    )
