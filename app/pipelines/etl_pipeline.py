"""
ETL Pipeline for FinTech Data Platform
Processes PaySim financial transaction data for fraud detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from typing import Dict, List, Optional
import json
import os

from app.core.config import settings
from app.models.fraud_alert import FraudAlert

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinTechETL:
    """ETL pipeline for PaySim financial data processing"""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.paysim_file = "data/PS_20174392719_1491204439457_log.csv"
        
    def extract_paysim_data(self) -> pd.DataFrame:
        """Extract PaySim transaction data"""
        try:
            if not os.path.exists(self.paysim_file):
                logger.error(f"PaySim data file not found: {self.paysim_file}")
                raise FileNotFoundError(f"PaySim data file not found: {self.paysim_file}")
            
            # Read PaySim data
            df = pd.read_csv(self.paysim_file)
            
            logger.info(f"Extracted {len(df)} PaySim transactions")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting PaySim data: {e}")
            raise
    
    def transform_paysim_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform PaySim data with business logic"""
        try:
            # Create a copy to avoid modifying original
            transformed_df = df.copy()
            
            # Rename columns to match our schema
            column_mapping = {
                'step': 'time_step',
                'type': 'transaction_type',
                'amount': 'amount',
                'nameOrig': 'sender_id',
                'oldbalanceOrg': 'sender_old_balance',
                'newbalanceOrig': 'sender_new_balance',
                'nameDest': 'receiver_id',
                'oldbalanceDest': 'receiver_old_balance',
                'newbalanceDest': 'receiver_new_balance',
                'isFraud': 'is_fraud',
                'isFlaggedFraud': 'is_flagged_fraud'
            }
            transformed_df = transformed_df.rename(columns=column_mapping)
            
            # Add derived columns
            transformed_df['transaction_date'] = pd.to_datetime('2017-01-01') + pd.to_timedelta(transformed_df['time_step'], unit='h')
            transformed_df['transaction_hour'] = transformed_df['time_step'] % 24
            transformed_df['transaction_day'] = transformed_df['time_step'] // 24
            
            # Add transaction categories
            transformed_df['amount_category'] = pd.cut(
                transformed_df['amount'],
                bins=[0, 100, 1000, 10000, float('inf')],
                labels=['small', 'medium', 'large', 'very_large']
            )
            
            # Add fraud risk indicators
            transformed_df['high_value_transaction'] = transformed_df['amount'] > 10000
            transformed_df['unusual_amount'] = transformed_df['amount'] > transformed_df['amount'].quantile(0.95)
            transformed_df['balance_change_ratio'] = abs(transformed_df['sender_new_balance'] - transformed_df['sender_old_balance']) / (transformed_df['sender_old_balance'] + 1)
            
            # Add risk score (simple heuristic)
            transformed_df['risk_score'] = (
                (transformed_df['is_fraud'] * 0.8) +
                (transformed_df['high_value_transaction'] * 0.3) +
                (transformed_df['unusual_amount'] * 0.2) +
                (transformed_df['balance_change_ratio'] > 0.5) * 0.1
            )
            
            logger.info(f"Transformed {len(transformed_df)} PaySim transactions")
            return transformed_df
            
        except Exception as e:
            logger.error(f"Error transforming PaySim data: {e}")
            raise
    
    def calculate_fraud_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate fraud detection metrics"""
        try:
            metrics = {}
            
            # Basic transaction metrics
            total_transactions = len(df)
            total_fraud = df['is_fraud'].sum()
            fraud_rate = total_fraud / total_transactions if total_transactions > 0 else 0
            
            # Transaction type analysis
            transaction_types = df['transaction_type'].value_counts()
            
            # Fraud by transaction type
            fraud_by_type = df[df['is_fraud'] == 1]['transaction_type'].value_counts()
            
            # Amount analysis
            avg_amount = df['amount'].mean()
            fraud_amount = df[df['is_fraud'] == 1]['amount'].mean()
            
            # Risk score analysis
            avg_risk_score = df['risk_score'].mean()
            high_risk_transactions = len(df[df['risk_score'] > 0.5])
            
            metrics = {
                'total_transactions': total_transactions,
                'total_fraud': total_fraud,
                'fraud_rate': fraud_rate,
                'transaction_types': transaction_types.to_dict(),
                'fraud_by_type': fraud_by_type.to_dict(),
                'avg_amount': avg_amount,
                'fraud_amount': fraud_amount,
                'avg_risk_score': avg_risk_score,
                'high_risk_transactions': high_risk_transactions
            }
            
            logger.info(f"Calculated fraud metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating fraud metrics: {e}")
            raise
    
    def load_to_data_lake(self, df: pd.DataFrame, table_name: str, date: datetime) -> None:
        """Load processed data to data lake (MinIO)"""
        try:
            # Create partitioned file path
            date_str = date.strftime("%Y-%m-%d")
            file_path = f"data/{table_name}/date={date_str}/{table_name}_{date_str}.parquet"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert to Parquet format
            df.to_parquet(file_path, index=False)
            
            logger.info(f"Loaded {len(df)} records to {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading to data lake: {e}")
            raise
    
    def run_daily_etl(self, date: Optional[datetime] = None) -> Dict:
        """Run complete daily ETL pipeline with PaySim data"""
        try:
            if date is None:
                date = datetime.now() - timedelta(days=1)
            
            logger.info(f"Starting PaySim ETL for {date.date()}")
            
            # Extract PaySim data
            paysim_df = self.extract_paysim_data()
            
            # Transform data
            transformed_df = self.transform_paysim_data(paysim_df)
            
            # Calculate metrics
            fraud_metrics = self.calculate_fraud_metrics(transformed_df)
            
            # Load to data lake
            self.load_to_data_lake(transformed_df, 'paysim_transactions', date)
            
            # Save metrics
            metrics_df = pd.DataFrame([fraud_metrics])
            self.load_to_data_lake(metrics_df, 'fraud_metrics', date)
            
            logger.info(f"Completed PaySim ETL for {date.date()}")
            
            return {
                'status': 'success',
                'date': date.date().isoformat(),
                'transactions_processed': len(paysim_df),
                'fraud_alerts_processed': fraud_metrics['total_fraud'],
                'metrics': fraud_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in PaySim ETL: {e}")
            return {
                'status': 'error',
                'date': date.date().isoformat() if date else None,
                'error': str(e)
            }


# Main execution
if __name__ == "__main__":
    etl = FinTechETL()
    result = etl.run_daily_etl()
    print(json.dumps(result, indent=2))
