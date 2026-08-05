from fastapi import APIRouter

from ml_service.database import get_db_connection

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
                    "user_agent": r[7],
                }
                for r in rows
            ]
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    finally:
        conn.close()


@db_router.get("/prompts")
def get_prompts():
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, timestamp, model, prompt, ip, user_agent
                FROM prompt_logs 
                ORDER BY id DESC 
                LIMIT 50
                """
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1].isoformat(),
                    "model": r[2],
                    "prompt": r[3],
                    "ip": r[4],
                    "user_agent": r[5],
                }
                for r in rows
            ]
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    finally:
        conn.close()


@db_router.get("/stats")
def get_stats():
    """
    Получить сводную статистику из ETL таблиц
    """
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_days,
                    SUM(total_predictions) as total_predictions,
                    AVG(avg_confidence) as avg_confidence,
                    AVG(avg_processing_time) as avg_processing_time
                FROM etl_daily_stats
            """)
            overall = cur.fetchone()

            cur.execute("""
                SELECT 
                    date,
                    total_predictions,
                    avg_confidence,
                    avg_processing_time,
                    unique_ips
                FROM etl_daily_stats
                ORDER BY date DESC
                LIMIT 7
            """)
            last_7_days = cur.fetchall()

            cur.execute("""
                SELECT 
                    COUNT(*) as total_prompts,
                    COUNT(DISTINCT model) as unique_models
                FROM prompt_logs
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
            """)
            prompts = cur.fetchone()

            return {
                "total_predictions": overall[1] or 0,
                "avg_confidence": round(overall[2], 4) if overall[2] else 0,
                "avg_processing_time_ms": round(overall[3], 2) if overall[3] else 0,
                "last_7_days": [
                    {
                        "date": r[0].isoformat(),
                        "predictions": r[1] or 0,
                        "confidence": round(r[2], 4) if r[2] else 0,
                        "avg_time_ms": round(r[3], 2) if r[3] else 0,
                        "unique_ips": r[4] or 0,
                    }
                    for r in last_7_days
                ],
                "prompts_last_24h": prompts[0] or 0 if prompts else 0,
                "unique_models_24h": prompts[1] or 0 if prompts else 0,
            }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    finally:
        conn.close()
