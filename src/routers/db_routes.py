from fastapi import APIRouter

from src.database import get_db_connection

db_router = APIRouter()

@db_router.get("/logs")
def get_logs():
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, timestamp, features, prediction, confidence, "
                "processing_time_ms, ip, user_agent "
                "FROM predict_logs ORDER BY id DESC LIMIT 10"
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1].isoformat(),
                    "features": r[2],
                    "prediction": r[3],
                    "confidence": r[4],
                    "processing_time_ms": r[5],
                    "ip": r[6],
                    "user_agent": r[7]
                }
                for r in rows
            ]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
