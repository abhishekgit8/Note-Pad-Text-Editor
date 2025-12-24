from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

# Load environment variables from .env (file in same directory as this module)
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Strip trailing/leading whitespace if present
if USER: USER = USER.strip()
if PASSWORD: PASSWORD = PASSWORD.strip()
if HOST: HOST = HOST.strip()
if PORT: PORT = PORT.strip()
if DBNAME: DBNAME = DBNAME.strip()

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)
# Create SessionLocal class for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from models and create tables (if they don't exist)
from models import Base
Base.metadata.create_all(bind=engine)

# If using Transaction Pooler or Session Pooler, we want to ensure we disable SQLAlchemy client side pooling -
# https://docs.sqlalchemy.org/en/20/core/pooling.html#switching-pool-implementations
# engine = create_engine(DATABASE_URL, poolclass=NullPool)

# Test the connection (run on import to surface connection errors early)
try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")