import sys
from pathlib import Path

# allow running this script directly from the project root: python scripts/init_db.py
# bc need models from app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base
from app import models

def init_database():
    print("connecting to cloud db and creating table...")

    Base.metadata.create_all(bind=engine)

    print("success!")

if __name__ == "__main__":
    init_database()
