from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from models.ranking import UniversityRankingDB
from models.base import Base
from schemas.ranking import RankingsResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Ensure table exists
Base.metadata.create_all(bind=engine)


def save_rankings_to_db(rankings_response: RankingsResponse) -> None:
    """
    Persist validated university rankings into PostgreSQL.
    """

    session = SessionLocal()

    try:
        for uni in rankings_response.rankings:
            db_row = UniversityRankingDB(
                rank=uni.rank,
                institution=uni.institution,
                state=uni.state,
                peer_assessment_score=uni.peer_assessment_score,
            )
            session.add(db_row)

        session.commit()
        print(f"✅ Saved {len(rankings_response.rankings)} university rankings")

    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Database error")
        raise e

    except Exception as e:
        session.rollback()
        print("❌ Unexpected error")
        raise e

    finally:
        session.close()
