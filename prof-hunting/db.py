import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Import all models here to register them with Base
from models.ranking import UniversityRankingDB
from models.faculty import FacultyRegistryDB
from models.research import ResearchRegistryDB

# Create all tables (SQLAlchemy will respect dependencies)
Base.metadata.create_all(bind=engine)
