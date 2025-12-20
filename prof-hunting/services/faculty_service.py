import json
import os
from dotenv import load_dotenv
from perplexity import Perplexity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from schemas.faculty import FacultyRegistryResponse
from models.faculty import FacultyRegistryDB, Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

client = Perplexity(api_key=PERPLEXITY_API_KEY)


def fetch_faculty_registry(university: str) -> FacultyRegistryResponse:
    """
    Fetch faculty registry for a given university using Perplexity.
    Research quality rating is normalized to a 0–10 scale.
    """

    schema = {
        "type": "object",
        "properties": {
            "faculty": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "university": {"type": "string"},
                        "department": {"type": "string"},
                        "professor_name": {"type": "string"},
                        "academic_tier": {"type": "string"},
                        "research_focus": {"type": "string"},
                        "future_job_prospect": {"type": "string"},
                        "profile_link": {"type": "string"},
                        "email": {"type": "string"},
                        # 🔥 UPDATED SCALE
                        "research_quality_rating": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 10,
                            "description": (
                                "Overall research quality score on a 0–10 scale "
                                "based on publication quality, impact, and reputation."
                            ),
                        },
                        "funding_focus_rating": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 10,
                        },
                        "lab_members_page": {"type": "string"},
                        "top_venues": {"type": "string"},
                        "public_metrics": {"type": "string"},
                        "best_ta_ra_profile": {"type": "string"},
                        "best_paper": {"type": "string"},
                    },
                    "required": [
                        "university",
                        "department",
                        "professor_name",
                        "academic_tier",
                        "research_focus",
                        "future_job_prospect",
                        "research_quality_rating",
                        "funding_focus_rating",
                        "top_venues",
                        "best_paper",
                    ],
                },
            }
        },
        "required": ["faculty"],
    }

    completion = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {
                "role": "user",
                "content": (
                    f"List top Computer Science professors at {university} "
                    "focused on Data Science / Machine Learning. "
                    "Only use publicly available information. "
                    "Rate research quality on a strict 0–10 scale."
                ),
            }
        ],
        response_format={"type": "json_schema", "json_schema": {"schema": schema}},
    )

    data = json.loads(completion.choices[0].message.content)

    return FacultyRegistryResponse(**data)


def save_faculty_registry(response: FacultyRegistryResponse) -> None:
    session = SessionLocal()
    try:
        for f in response.faculty:
            row = FacultyRegistryDB(**f.model_dump())
            session.add(row)

        session.commit()
        print(f"✅ Saved {len(response.faculty)} faculty records")

    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError("Faculty registry DB write failed") from e
    finally:
        session.close()
