#!/usr/bin/env python
"""
Script to run database migrations for invoice-service
This script connects to AWS RDS PostgreSQL 16 instance and runs Alembic migrations
"""
import os
import sys
import time
import logging
from pathlib import Path
from subprocess import run, PIPE, CalledProcessError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("invoice-service-migrations")

def wait_for_db(max_retries=30, retry_interval=5):
    """
    Wait for the database to become available
    AWS RDS may take some time to accept connections after initialization
    """
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    # Get database URL from environment
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    retries = 0
    connected = False
    
    # Extract connection parameters from URL
    parts = db_url.split("//")[1].split("@")
    credentials = parts[0].split(":")
    host_port_db = parts[1].split("/")
    
    username = credentials[0]
    password = credentials[1]
    host_port = host_port_db[0].split(":")
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 5432
    dbname = host_port_db[1]
    
    # Test connection with retry logic
    while not connected and retries < max_retries:
        try:
            logger.info(f"Trying to connect to database (attempt {retries+1}/{max_retries})...")
            conn = psycopg2.connect(
                user=username,
                password=password,
                host=host,
                port=port,
                dbname=dbname,
                connect_timeout=10
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    connected = True
                    logger.info("Successfully connected to database")
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to connect to database: {e}")
            retries += 1
            if retries < max_retries:
                logger.info(f"Waiting {retry_interval} seconds before retrying...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Could not connect to database after {max_retries} attempts")
                sys.exit(1)

def run_migrations():
    """Run Alembic migrations"""
    try:
        # First, make sure we're in the right directory
        os.chdir(Path(__file__).parent)
        
        # Wait for database to be ready
        wait_for_db()
        
        # Ensure migrations directory exists
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            logger.info("Initializing Alembic for first time use...")
            os.makedirs(migrations_dir, exist_ok=True)
            
            # Initialize Alembic
            init_result = run(
                ["alembic", "init", "migrations/alembic"],
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )
            
            if init_result.returncode != 0:
                logger.error("Failed to initialize Alembic")
                logger.error(init_result.stderr)
                sys.exit(1)
                
            # Create a sample alembic.ini
            with open("migrations/alembic.ini", "w") as f:
                f.write("""[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Output formatting
truncate_slug_length = 40
revision_environment = false
sourceless = false
sqlalchemy.url = 

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")
            
            # Create env.py file
            alembic_dir = migrations_dir / "alembic"
            if not (alembic_dir / "env.py").exists():
                os.makedirs(alembic_dir, exist_ok=True)
                env_py_content = """import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.pool import QueuePool

from alembic import context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set SQLAlchemy URL from environment variable (AWS RDS PostgreSQL 16)
db_url = os.environ.get("DATABASE_URL", "postgresql://invoice_user:invoice_password@localhost:5432/invoice_service_db")
config.set_main_option("sqlalchemy.url", db_url)

# Configure PostgreSQL connection options for AWS RDS
sqlalchemy_config = config.get_section(config.config_ini_section)
sqlalchemy_config["sqlalchemy.pool_size"] = "5"
sqlalchemy_config["sqlalchemy.max_overflow"] = "10"
sqlalchemy_config["sqlalchemy.pool_timeout"] = "30"
sqlalchemy_config["sqlalchemy.pool_recycle"] = "1800"
sqlalchemy_config["sqlalchemy.pool_pre_ping"] = "True"

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.db.database import Base
# Import all models here to ensure they are registered with the metadata
from app.models import *

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
                with open(alembic_dir / "env.py", "w") as f:
                    f.write(env_py_content)
        
        # Run migrations with optimized parameters for AWS RDS
        logger.info("Running database migrations...")
        
        # Create version table if not exists (allows Alembic to initialize correctly)
        run(["alembic", "-c", "migrations/alembic.ini", "current"], check=True)
        
        # Create initial migration if none exists
        versions_dir = Path("migrations/alembic/versions")
        if not versions_dir.exists() or not any(versions_dir.glob("*.py")):
            logger.info("Creating initial migration...")
            os.makedirs(versions_dir, exist_ok=True)
            result = run(
                ["alembic", "-c", "migrations/alembic.ini", "revision", "--autogenerate", "-m", "initial"],
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )
            if result.returncode == 0:
                logger.info("Initial migration created")
            else:
                logger.error("Failed to create initial migration")
                logger.error(result.stderr)
                sys.exit(1)
        
        # Upgrade to latest version
        result = run(
            ["alembic", "-c", "migrations/alembic.ini", "upgrade", "head"],
            stdout=PIPE,
            stderr=PIPE,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Database migration failed with code {result.returncode}")
            logger.error(result.stderr)
            sys.exit(1)
    
    except CalledProcessError as e:
        logger.error(f"Error running migrations: {e}")
        logger.error(e.stderr if hasattr(e, 'stderr') else "No error output available")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
