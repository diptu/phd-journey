from sqlalchemy import Column, Integer, String, Float, Index
from .base import Base


class UniversityRankingDB(Base):
    __tablename__ = "cs_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rank = Column(Integer, nullable=False, index=True)
    institution = Column(String, nullable=False, unique=True, index=True)
    state = Column(String(2), nullable=False, index=True)
    peer_assessment_score = Column(Float, nullable=False)
