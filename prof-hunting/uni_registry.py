import json
import os
from dotenv import load_dotenv
from perplexity import Perplexity
from pydantic import ValidationError

from schemas.ranking import RankingsResponse
from services.ranking_service import save_rankings_to_db


def main() -> None:
    """
    Main ingestion pipeline:
    Perplexity → JSON → Pydantic → PostgreSQL
    """

    # -----------------------------
    # Load environment variables
    # -----------------------------
    load_dotenv()

    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY is not set in .env")

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in .env")

    # -----------------------------
    # Initialize Perplexity Client
    # -----------------------------
    try:
        client = Perplexity(api_key=PERPLEXITY_API_KEY)
    except Exception as e:
        raise RuntimeError("Failed to initialize Perplexity client") from e

    # -----------------------------
    # Define response schema
    # -----------------------------
    ranking_schema = {
        "type": "object",
        "properties": {
            "rankings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rank": {"type": "integer"},
                        "institution": {"type": "string"},
                        "state": {
                            "type": "string",
                            "description": "2-letter US abbreviation",
                        },
                        "peer_assessment_score": {"type": "number"},
                    },
                    "required": [
                        "rank",
                        "institution",
                        "state",
                        "peer_assessment_score",
                    ],
                },
            }
        },
        "required": ["rankings"],
    }

    # -----------------------------
    # Call Perplexity API
    # -----------------------------
    try:
        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Extract all the Computer Science graduate school rankings from US News: "
                        "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings"
                    ),
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"schema": ranking_schema},
            },
        )
    except Exception as e:
        raise RuntimeError("Perplexity API request failed") from e

    # -----------------------------
    # Parse JSON response
    # -----------------------------
    try:
        raw_content = completion.choices[0].message.content
        data = json.loads(raw_content)
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        raise RuntimeError("Failed to parse Perplexity response JSON") from e

    # -----------------------------
    # Validate with Pydantic
    # -----------------------------
    try:
        rankings_response = RankingsResponse(**data)
    except ValidationError as e:
        raise RuntimeError("Response validation failed") from e

    # -----------------------------
    # Persist to Database
    # -----------------------------
    try:
        save_rankings_to_db(rankings_response)
    except Exception as e:
        raise RuntimeError("Failed to persist rankings to database") from e

    print("🎉 University rankings ingestion completed successfully!")


# -----------------------------
# Script Entry Point
# -----------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("❌ Ingestion pipeline failed")
        print(f"Reason: {err}")
        exit(1)
