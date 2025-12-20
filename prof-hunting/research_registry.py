# research_registry.py
import os
from dotenv import load_dotenv
from perplexity import Perplexity
from sqlalchemy.orm import Session
from services.research_service import (
    fetch_recent_research_batch,
    save_research_registry,
    SessionLocal,
)
from schemas.research import ResearchRegistryResponse

# -----------------------------
# Load env variables
# -----------------------------
load_dotenv()
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))
PAPER_COUNT = int(os.getenv("PAPER_COUNT", 5))
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not PERPLEXITY_API_KEY or not DATABASE_URL:
    raise RuntimeError("PERPLEXITY_API_KEY and DATABASE_URL must be set in .env")

# -----------------------------
# Define interests and venues
# -----------------------------
TOP_VENUES = [
    # "OSDI",
    "SOSP",
    "EuroSys",
    "ASPLOS",
    # "NSDI",
    # "MLSys",
    # "NeurIPS",
    # "ICLR",
    # "ICML",
    # "SIGMOD",
    # "VLDB",
    # "ICDCS",
    # "HPDC",
    # "TPDS",
    # "TOCS",
    # "JMLR",
    # "TNSM",
    # "IoT-J",
]

INTEREST_KEYWORDS = [
    "Memory Disaggregation",
    "Distributed ML Training",
    "Inference at Scale",
    "ML-driven Scheduling",
    "Resource Orchestration",
    "Cloud-Edge ML",
    "Hardware Accelerators for Distributed Systems",
]

# -----------------------------
# Main ingestion
# -----------------------------
if __name__ == "__main__":
    client = Perplexity(api_key=PERPLEXITY_API_KEY)
    session: Session = SessionLocal()
    try:
        print("📚 Fetching research papers for each venue × keyword combination...")

        batch_counter = 0

        for venue in TOP_VENUES:
            for keyword in INTEREST_KEYWORDS:
                print(
                    f"🔹 Processing combination: Venue='{venue}', Keyword='{keyword}'"
                )

                # Fetch papers for this single combination
                research_data = fetch_recent_research_batch(
                    top_venues=[venue],  # pass as single-item list
                    interest_keywords=[keyword],  # pass as single-item list
                    top_n=PAPER_COUNT,
                    start_year=2020,
                    end_year=2025,
                    client=client,
                )

                total_papers = len(research_data.papers)
                if total_papers == 0:
                    print(f"⚠️ No papers found for Venue='{venue}', Keyword='{keyword}'")
                    continue

                # Save in batches
                for i in range(0, total_papers, BATCH_SIZE):
                    batch = ResearchRegistryResponse(
                        papers=research_data.papers[i : i + BATCH_SIZE]
                    )
                    batch_counter += 1
                    print(
                        f"📦 Saving batch {batch_counter} ({len(batch.papers)} papers)"
                    )
                    save_research_registry(batch, INTEREST_KEYWORDS, session=session)

        print("🎉 Research registry ingestion completed")

    finally:
        session.close()
