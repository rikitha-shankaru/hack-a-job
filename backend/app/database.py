from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.pool import QueuePool
from app.config import settings

# Optimized engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=False,  # Disable SQL logging in production for performance
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Max connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "connect_timeout": 10,
        "application_name": "hack-a-job"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import User for type hints (moved to avoid circular import)
try:
    from app.models import User
except ImportError:
    # Models not loaded yet, will be available at runtime
    User = None

# Optimize queries with eager loading
def optimize_user_query(query):
    """Optimize user queries with eager loading to prevent N+1"""
    if User:
        return query.options(joinedload(User.profile))
    return query

def optimize_job_query(query):
    """Optimize job queries"""
    return query

