from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import time
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Connection pool settings optimized for AWS RDS PostgreSQL 16
db_pool_config = {
    "pool_size": 5,  # Default number of connections to maintain in the pool
    "max_overflow": 10,  # Maximum number of connections beyond pool_size
    "pool_timeout": 30,  # Seconds to wait for a connection from the pool
    "pool_recycle": 1800,  # Recycle connections after 30 minutes
    "pool_pre_ping": True,  # Enable connection health checks
}

# Create SQLAlchemy engine with optimized settings for PostgreSQL 16
engine = create_engine(
    str(settings.DATABASE_URL),
    poolclass=QueuePool,
    connect_args={
        "sslmode": "prefer",  # Enable SSL for RDS connections
        "application_name": settings.PROJECT_NAME,  # Identify application in PostgreSQL logs
    },
    **db_pool_config
)

# Add event listeners for connection monitoring
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.info("Database connection established")
    connection_record.info['created'] = time.time()

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    # Check connection freshness - if older than 3 hours, recycle
    connection_age = time.time() - connection_record.info.get('created', time.time())
    if connection_age > 10800:  # 3 hours
        logger.info("Recycling database connection due to age")
        connection_proxy._pool.dispose()
        raise DisconnectionError("Connection too old")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Define custom DisconnectionError
class DisconnectionError(Exception):
    pass

def get_db():
    """
    Dependency for FastAPI routes to get a database session
    with automatic reconnection on failure
    """
    db = SessionLocal()
    try:
        # Test connection is valid
        db.execute("SELECT 1")
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        db.close()
        # Create a new connection
        db = SessionLocal()
        yield db
    finally:
        db.close()
