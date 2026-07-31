import os
import psycopg2


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
        print(f"DB Connection Error: {e}")
        return None


def init_db():
    """Создает таблицу при первом запуске."""
    conn = get_db_connection()
    if conn:
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
                    );
                """)
        except Exception as e:
            print(f"Failed to create table: {e}")
        finally:
            conn.close()
