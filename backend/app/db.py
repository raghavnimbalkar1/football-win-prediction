import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Load the environment variables from the .env file
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 2. Safely URL-encode the password to handle special characters like '@'
SAFE_PASSWORD = urllib.parse.quote_plus(DB_PASSWORD)

# 3. Construct the MySQL connection URL
# Format: mysql+pymysql://user:password@host:port/database
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{SAFE_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 4. Create the SQLAlchemy Engine
engine = create_engine(DATABASE_URL, echo=False)

# 5. Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. Dependency to get the DB session (We will use this later with FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            print("SUCCESS: Connected to the MySQL database!")
    except Exception as e:
        print(f"ERROR: Could not connect to the database.\nDetails: {e}")