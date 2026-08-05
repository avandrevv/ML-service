import json
import logging
import os
import time

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLService:
    def __init__(self):
        self.db_url = f"postgresql://postgres:{os.getenv('PGPASSWORD', 'postgres')}@db:5432/predict_logs_db"
        self.engine = create_engine(self.db_url)
        self.interval = int(os.getenv("ETL_INTERVAL", "30"))

    def extract_transform_load(self):
        """Основной ETL процесс"""
        try:
            with self.engine.connect() as conn:
                logger.info("Extracting data...")
                result = conn.execute(
                    text("""
                        SELECT 
                            id,
                            timestamp,
                            features,
                            prediction,
                            confidence,
                            processing_time_ms,
                            ip,
                            user_agent,
                            DATE(timestamp) as date
                        FROM predict_logs 
                        WHERE timestamp > NOW() - INTERVAL '1 hour'
                        ORDER BY id DESC
                    """)
                )
                rows = result.fetchall()

                if not rows:
                    logger.info("No new data to process")
                    return

                df = pd.DataFrame(rows, columns=result.keys())

                logger.info(f"Transforming {len(df)} records...")

                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["hour"] = df["timestamp"].dt.hour
                df["day_of_week"] = df["timestamp"].dt.dayofweek
                df["date"] = df["timestamp"].dt.date

                df["feature_count"] = df["features"].apply(
                    lambda x: len(x) if isinstance(x, (dict, list)) else 0
                )

                df["confidence_level"] = pd.cut(
                    df["confidence"],
                    bins=[0, 0.5, 0.7, 0.9, 1.0],
                    labels=["low", "medium", "high", "very_high"],
                )

                logger.info("Loading transformed data...")

                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS etl_aggregated (
                        id SERIAL PRIMARY KEY,
                        date DATE,
                        hour INTEGER,
                        day_of_week INTEGER,
                        total_predictions INTEGER,
                        avg_confidence FLOAT,
                        avg_processing_time FLOAT,
                        prediction_distribution JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                )

                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS etl_daily_stats (
                        id SERIAL PRIMARY KEY,
                        date DATE UNIQUE,
                        total_predictions INTEGER,
                        avg_confidence FLOAT,
                        avg_processing_time FLOAT,
                        unique_ips INTEGER,
                        model_performance JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                )

                agg_df = (
                    df.groupby(["date", "hour", "day_of_week"])
                    .agg(
                        {
                            "id": "count",
                            "confidence": "mean",
                            "processing_time_ms": "mean",
                            "prediction": lambda x: x.value_counts().to_dict(),
                        }
                    )
                    .reset_index()
                )

                for _, row in agg_df.iterrows():
                    conn.execute(
                        text("""
                        INSERT INTO etl_aggregated 
                        (date, hour, day_of_week, total_predictions, 
                         avg_confidence, avg_processing_time, prediction_distribution)
                        VALUES (:date, :hour, :day_of_week, :total_predictions,
                                :avg_confidence, :avg_processing_time, :prediction_distribution)
                    """),
                        {
                            "date": row["date"],
                            "hour": int(row["hour"]),
                            "day_of_week": int(row["day_of_week"]),
                            "total_predictions": int(row["id"]),
                            "avg_confidence": float(row["confidence"]),
                            "avg_processing_time": float(row["processing_time_ms"]),
                            "prediction_distribution": json.dumps(row["prediction"]),
                        },
                    )

                daily_stats = (
                    df.groupby("date")
                    .agg(
                        {
                            "id": "count",
                            "confidence": "mean",
                            "processing_time_ms": "mean",
                            "ip": "nunique",
                            "prediction": lambda x: {
                                "0": int((x == 0).sum()),
                                "1": int((x == 1).sum()),
                            },
                        }
                    )
                    .reset_index()
                )

                for _, row in daily_stats.iterrows():
                    conn.execute(
                        text("""
                        INSERT INTO etl_daily_stats 
                        (date, total_predictions, avg_confidence, avg_processing_time, 
                         unique_ips, model_performance)
                        VALUES (:date, :total_predictions, :avg_confidence, 
                                :avg_processing_time, :unique_ips, :model_performance)
                        ON CONFLICT (date) DO UPDATE SET
                            total_predictions = EXCLUDED.total_predictions,
                            avg_confidence = EXCLUDED.avg_confidence,
                            avg_processing_time = EXCLUDED.avg_processing_time,
                            unique_ips = EXCLUDED.unique_ips,
                            model_performance = EXCLUDED.model_performance,
                            created_at = NOW()
                    """),
                        {
                            "date": row["date"],
                            "total_predictions": int(row["id"]),
                            "avg_confidence": float(row["confidence"]),
                            "avg_processing_time": float(row["processing_time_ms"]),
                            "unique_ips": int(row["ip"]),
                            "model_performance": json.dumps(row["prediction"]),
                        },
                    )

                conn.commit()
                logger.info(f"ETL completed successfully. Processed {len(df)} records.")

        except Exception as e:
            logger.error(f"ETL error: {e}")
            raise

    def run(self):
        """Запуск ETL процесса в цикле"""
        logger.info(f"Starting ETL service with interval {self.interval}s")
        while True:
            try:
                self.extract_transform_load()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                logger.info("Stopping ETL service...")
                break
            except Exception as e:  # noqa: BLE001
                logger.error(f"ETL service error: {e}")
                time.sleep(10)


if __name__ == "__main__":
    etl = ETLService()
    etl.run()
