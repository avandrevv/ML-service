import os
import psycopg2
from psycopg2.extras import Json
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "predict_logs_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            connect_timeout=3
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"DB Connection Error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for initialization")
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS predict_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    features JSONB,
                    prediction INTEGER,
                    confidence FLOAT,
                    processing_time_ms FLOAT,
                    ip VARCHAR(45),
                    user_agent TEXT
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prompt_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    model VARCHAR(100),
                    prompt TEXT,
                    ip VARCHAR(45),
                    user_agent TEXT
                )
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompt_logs_timestamp 
                ON prompt_logs(timestamp DESC)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_predict_logs_timestamp 
                ON predict_logs(timestamp DESC)
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    finally:
        conn.close()
        