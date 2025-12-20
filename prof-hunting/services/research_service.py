# research_service.py
import json
import os
from typing import List
from dotenv import load_dotenv
from perplexity import Perplexity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# -----------------------------
# Import models in correct order
# -----------------------------
from models.base import Base  # Single Base
from models.ranking import UniversityRankingDB
from models.faculty import FacultyRegistryDB
from models.research import ResearchRegistryDB
from models.enums import ReviewFeedbackEnum
from schemas.research import ResearchRegistryResponse

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not DATABASE_URL or not PERPLEXITY_API_KEY:
    raise RuntimeError("DATABASE_URL and PERPLEXITY_API_KEY must be set in .env")

# -----------------------------
# Initialize Perplexity client
# -----------------------------
client = Perplexity(api_key=PERPLEXITY_API_KEY)

# -----------------------------
# Database setup
# -----------------------------
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Ensure all tables exist (FK dependencies handled correctly)
Base.metadata.create_all(bind=engine)


# -----------------------------
# Utility functions
# -----------------------------
def normalize_university(univ_str: str) -> str:
    """Normalize university name for DB insertion."""
    if not univ_str or univ_str.lower() in (
        "not specified",
        "not clearly identifiable",
    ):
        return None
    return univ_str.split(";")[0].strip()


# -----------------------------
# Fetch Research Papers
# -----------------------------
def fetch_recent_research_batch(
    top_venues: list[str],
    interest_keywords: list[str],
    top_n: int = 5,
    start_year: int = 2020,
    end_year: int = 2025,
    client: Perplexity | None = None,
) -> ResearchRegistryResponse:
    """
    Fetch top N papers for each combination of venues & keywords using Perplexity.
    """
    schema = {
        "type": "object",
        "properties": {
            "papers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "authors": {"type": "string"},
                        "venue": {"type": "string"},
                        "year": {"type": "integer"},
                        "focus_area": {"type": "string"},
                        "paper_link": {"type": "string"},
                        "abstract": {"type": "string"},
                        "university": {"type": "string"},
                        "impact_score": {"type": "number", "minimum": 0, "maximum": 10},
                    },
                    "required": [
                        "title",
                        "authors",
                        "venue",
                        "year",
                        "focus_area",
                        "paper_link",
                        "impact_score",
                    ],
                },
            }
        },
        "required": ["papers"],
    }

    all_papers = []

    for venue in top_venues:
        for keyword in interest_keywords:
            try:
                prompt = (
                    f"List the top {top_n} influential research papers published between {start_year} and {end_year} "
                    f"strictly relevant to ML-Enhanced Distributed Systems. "
                    f"Focus on this interest: {keyword}. "
                    f"Use this venue only: {venue}. "
                    "Include title, first author only as 'author', first author's university as 'university', "
                    "venue, year, focus_area, paper_link, abstract, and impact_score."
                )

                completion = client.chat.completions.create(
                    model="sonar-pro",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {"schema": schema},
                    },
                )

                raw_data = completion.choices[0].message.content
                parsed = json.loads(raw_data)
                papers = ResearchRegistryResponse(**parsed).papers

                print(
                    f"🔍 Retrieved {len(papers)} papers for venue='{venue}', keyword='{keyword}'"
                )
                all_papers.extend(papers)

            except Exception as e:
                print(
                    f"❌ Failed to fetch papers for venue='{venue}', keyword='{keyword}': {e}"
                )

    return ResearchRegistryResponse(papers=all_papers)


# -----------------------------
# Save Research Papers
# -----------------------------
def save_research_registry(
    data: ResearchRegistryResponse,
    interest_keywords: list[str],
    session: Session | None = None,
) -> None:
    """
    Save research papers to the database in batch.
    - Skips duplicates safely.
    - Handles missing universities gracefully.
    - Uses provided session if passed, otherwise creates a new one.
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        inserted = 0
        skipped = 0

        for paper in data.papers:
            # Skip duplicate papers
            exists = (
                session.query(ResearchRegistryDB)
                .filter(
                    ResearchRegistryDB.title == paper.title,
                    ResearchRegistryDB.venue == paper.venue,
                    ResearchRegistryDB.year == paper.year,
                )
                .first()
            )
            if exists:
                skipped += 1
                continue

            # Normalize university
            university_name = normalize_university(paper.university)
            if university_name:
                uni = (
                    session.query(UniversityRankingDB)
                    .filter_by(institution=university_name)
                    .first()
                )
                if not uni:
                    print(
                        f"⚠️ University '{university_name}' not found, skipping FK link"
                    )
                    university_name = None

            # Match interest keywords (only from provided list)
            matched_keywords = [
                kw
                for kw in interest_keywords
                if paper.focus_area and kw.lower() in paper.focus_area.lower()
            ]
            matched_keywords_str = (
                ",".join(matched_keywords) if matched_keywords else None
            )

            session.add(
                ResearchRegistryDB(
                    title=paper.title,
                    authors=paper.authors,
                    venue=paper.venue,
                    year=paper.year,
                    focus_area=paper.focus_area,
                    abstract=paper.abstract,
                    paper_link=paper.paper_link,
                    university=university_name,
                    impact_score=paper.impact_score,
                    interest_keywords=matched_keywords_str,
                    is_reviewed=paper.is_reviewed or False,
                    review_feedback=paper.review_feedback
                    or ReviewFeedbackEnum.NOT_READ,
                    review_notes=paper.review_notes,
                    faculty_id=None,
                )
            )
            inserted += 1

        session.commit()
        print(f"✅ Research registry saved | Inserted: {inserted}, Skipped: {skipped}")

    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Database error")
        raise e
    except Exception as e:
        session.rollback()
        print("❌ Unexpected error")
        raise e
    finally:
        if close_session:
            session.close()


# -----------------------------
# Update Paper Review
# -----------------------------
def update_paper_review(
    paper_id: int, feedback: ReviewFeedbackEnum, notes: str | None = None
) -> None:
    """
    Update review status for a paper.
    """
    session: Session = SessionLocal()
    try:
        paper = session.get(ResearchRegistryDB, paper_id)
        if not paper:
            raise ValueError(f"Paper with id={paper_id} not found")

        paper.is_reviewed = True
        paper.review_feedback = feedback
        paper.review_notes = notes

        session.commit()
        print(f"📝 Review updated for paper id={paper_id}")

    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Database error during review update")
        raise e
    except Exception as e:
        session.rollback()
        print("❌ Unexpected error during review update")
        raise e
    finally:
        session.close()
