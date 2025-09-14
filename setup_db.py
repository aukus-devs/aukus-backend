from pathlib import Path
from sqlalchemy import create_engine
from src.db.db_models import DbBase

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = "./sqlite"
DATABASE_URL = f"sqlite:///{DB_PATH}"

def setup_db():
    engine = create_engine(DATABASE_URL, echo=False)
    DbBase.metadata.create_all(engine)

if __name__ == "__main__":
    setup_db()
    print(f"Database created at {DB_PATH}")
