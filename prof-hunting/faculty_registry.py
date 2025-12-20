from services.faculty_service import (
    fetch_faculty_registry,
    save_faculty_registry,
)

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tqdm import tqdm
import os


def get_all_universities() -> list[str]:
    """
    Fetch distinct universities from the University Registry table.
    """
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    engine = create_engine(DATABASE_URL)

    query = """
        SELECT DISTINCT institution
        FROM cs_rankings
        ORDER BY institution;
    """

    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [row[0] for row in result.fetchall()]


def main() -> None:
    universities = get_all_universities()

    print(f"🏫 Found {len(universities)} universities to process\n")

    # Progress bar
    for university in tqdm(
        universities,
        desc="📊 Processing Universities",
        unit="university",
    ):
        try:
            faculty_data = fetch_faculty_registry(university)
            save_faculty_registry(faculty_data)

        except Exception as e:
            # Continue on failure
            tqdm.write(f"❌ Failed for {university}: {e}")
            continue

    print("\n🎓 Faculty registry ingestion completed for all universities")


if __name__ == "__main__":
    main()
