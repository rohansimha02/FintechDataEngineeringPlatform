"""
Prefect Flows for FinTech Data Platform
Orchestrates ETL pipelines, batch processing, and data transformations
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.blocks.system import Secret
import structlog

from app.core.database import get_db_session
from app.pipelines.etl_pipeline import ETLPipeline
from app.utils.data_validator import validate_transaction

logger = structlog.get_logger()

@task(cache_key_fn=task_input_hash)
def extract_daily_transactions(date: str) -> pd.DataFrame:
    """Extract transactions for a specific date"""
    logger = get_run_logger()
    logger.info("Extracting transactions", date=date)
    
    # Extract from PaySim data source
    query = f"""
    SELECT * FROM transactions 
    WHERE DATE(transaction_date) = '{date}'
    """
    
    with get_db_session() as session:
        df = pd.read_sql(query, session.bind)
    
    logger.info("Extraction completed", record_count=len(df))
    return df

@task
def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Transform transaction data"""
    logger = get_run_logger()
    logger.info("Transforming transactions", input_count=len(df))
    
    if df.empty:
        return df
    
    # Apply transformations for PaySim data
    df['amount_usd'] = df['amount'] * 1.1  # Convert to USD
    df['risk_category'] = pd.cut(
        df['risk_score'], 
        bins=[0, 0.3, 0.7, 1.0], 
        labels=['low', 'medium', 'high']
    )
    df['hour_of_day'] = df['transaction_hour']
    df['day_of_week'] = df['transaction_date'].dt.day_name()
    
    # Add data quality checks
    df['is_valid'] = df.apply(validate_transaction, axis=1)
    
    logger.info("Transformation completed", output_count=len(df))
    return df

@task
def load_transactions(df: pd.DataFrame, target_table: str = "transactions_processed"):
    """Load transformed transactions to target table"""
    logger = get_run_logger()
    logger.info("Loading transactions", table=target_table, count=len(df))
    
    if df.empty:
        logger.warning("No data to load")
        return
    
    with get_db_session() as session:
        # Create table if not exists for PaySim data
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {target_table} (
            id SERIAL PRIMARY KEY,
            time_step INTEGER,
            transaction_type VARCHAR(50),
            amount DECIMAL(10,2),
            amount_usd DECIMAL(10,2),
            sender_id VARCHAR(255),
            sender_old_balance DECIMAL(10,2),
            sender_new_balance DECIMAL(10,2),
            receiver_id VARCHAR(255),
            receiver_old_balance DECIMAL(10,2),
            receiver_new_balance DECIMAL(10,2),
            is_fraud BOOLEAN,
            is_flagged_fraud BOOLEAN,
            transaction_date TIMESTAMP,
            transaction_hour INTEGER,
            transaction_day INTEGER,
            amount_category VARCHAR(20),
            high_value_transaction BOOLEAN,
            unusual_amount BOOLEAN,
            balance_change_ratio DECIMAL(5,4),
            risk_score DECIMAL(3,2),
            risk_category VARCHAR(20),
            hour_of_day INTEGER,
            day_of_week VARCHAR(20),
            is_valid BOOLEAN,
            processed_at TIMESTAMP DEFAULT NOW()
        )
        """
        session.execute(create_table_sql)
        
        # Load data
        df.to_sql(target_table, session.bind, if_exists='append', index=False)
        session.commit()
    
    logger.info("Load completed", table=target_table)

@task
def run_dbt_transformation():
    """Run dbt transformations"""
    logger = get_run_logger()
    logger.info("Running dbt transformations")
    
    # In production, this would call dbt CLI
    # For now, we'll simulate the process
    import subprocess
    import os
    
    try:
        result = subprocess.run(
            ["dbt", "run", "--project-dir", "./dbt"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            logger.info("dbt transformations completed successfully")
        else:
            logger.error("dbt transformations failed", error=result.stderr)
            raise Exception("dbt transformation failed")
            
    except FileNotFoundError:
        logger.warning("dbt not found, skipping transformations")
    except Exception as e:
        logger.error("Error running dbt", error=str(e))
        raise

@task
def run_data_quality_checks(date: str):
    """Run data quality checks using Great Expectations"""
    logger = get_run_logger()
    logger.info("Running data quality checks", date=date)
    
    # Simulate Great Expectations checks
    # In production, this would use actual GE suite
    checks = [
        "check_transaction_amounts_not_null",
        "check_risk_scores_in_range",
        "check_timestamp_format",
        "check_merchant_names_not_empty"
    ]
    
    for check in checks:
        logger.info(f"Running check: {check}")
        # Simulate check execution
        time.sleep(0.1)
    
    logger.info("Data quality checks completed")

@task
def generate_daily_report(date: str) -> Dict[str, Any]:
    """Generate daily analytics report"""
    logger = get_run_logger()
    logger.info("Generating daily report", date=date)
    
    with get_db_session() as session:
        # Calculate daily metrics for PaySim data
        metrics_query = f"""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(amount) as total_volume,
            AVG(risk_score) as avg_risk_score,
            COUNT(CASE WHEN risk_score > 0.7 THEN 1 END) as high_risk_count
        FROM transactions_processed 
        WHERE DATE(transaction_date) = '{date}'
        """
        
        result = session.execute(metrics_query).fetchone()
        
        report = {
            'date': date,
            'total_transactions': result[0] or 0,
            'total_volume': float(result[1] or 0),
            'avg_risk_score': float(result[2] or 0),
            'high_risk_count': result[3] or 0,
            'generated_at': datetime.now().isoformat()
        }
    
    logger.info("Daily report generated", report=report)
    return report

@flow(name="daily-etl-pipeline")
def daily_etl_pipeline(date: str = None):
    """Main daily ETL pipeline flow"""
    if date is None:
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    logger = get_run_logger()
    logger.info("Starting daily ETL pipeline", date=date)
    
    try:
        # Extract
        raw_data = extract_daily_transactions(date)
        
        # Transform
        transformed_data = transform_transactions(raw_data)
        
        # Load
        load_transactions(transformed_data)
        
        # Run dbt transformations
        run_dbt_transformation()
        
        # Data quality checks
        run_data_quality_checks(date)
        
        # Generate report
        report = generate_daily_report(date)
        
        logger.info("Daily ETL pipeline completed successfully", date=date)
        return report
        
    except Exception as e:
        logger.error("Daily ETL pipeline failed", error=str(e), date=date)
        raise

@flow(name="backfill-pipeline")
def backfill_pipeline(start_date: str, end_date: str):
    """Backfill pipeline for historical data"""
    logger = get_run_logger()
    logger.info("Starting backfill pipeline", start_date=start_date, end_date=end_date)
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        logger.info("Processing backfill date", date=date_str)
        
        try:
            daily_etl_pipeline(date_str)
            logger.info("Backfill date completed", date=date_str)
        except Exception as e:
            logger.error("Backfill date failed", date=date_str, error=str(e))
            # Continue with next date instead of failing entire backfill
        
        current += timedelta(days=1)
    
    logger.info("Backfill pipeline completed", start_date=start_date, end_date=end_date)

@flow(name="fraud-detection-pipeline")
def fraud_detection_pipeline():
    """Real-time fraud detection pipeline"""
    logger = get_run_logger()
    logger.info("Starting fraud detection pipeline")
    
    # This would integrate with the Kafka consumer
    # For now, we'll simulate the process
    from app.streaming.kafka_consumer import fintech_consumer
    
    try:
        # Start the consumer
        fintech_consumer.start()
    except KeyboardInterrupt:
        logger.info("Fraud detection pipeline stopped by user")
    except Exception as e:
        logger.error("Fraud detection pipeline failed", error=str(e))
        raise
    finally:
        fintech_consumer.stop()

if __name__ == "__main__":
    # Example usage
    daily_etl_pipeline()
