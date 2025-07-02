#!/usr/bin/env python
"""
Script to run database migrations for tax-service
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
logger = logging.getLogger("tax-service-migrations")

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
        
        # Run migrations with optimized parameters for AWS RDS
        logger.info("Running database migrations...")
        
        # Create version table if not exists (allows Alembic to initialize correctly)
        run(["alembic", "-c", "migrations/alembic.ini", "current"], check=True)
        
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
