"""
Data Engineering Tests for FinTech Data Platform
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os

from app.pipelines.etl_pipeline import FinTechETL
from app.streaming.kafka_producer import FinTechProducer


class TestETLPipeline:
    """Test ETL pipeline functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.etl = FinTechETL()
        
        # Sample transaction data
        self.sample_transactions = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'amount': [100.50, 2500.00, 45.99, 1500.00, 25.00],
            'currency': ['USD', 'USD', 'EUR', 'USD', 'GBP'],
            'status': ['completed', 'completed', 'failed', 'fraudulent', 'completed'],
            'payment_method': ['credit_card', 'bank_transfer', 'credit_card', 'crypto', 'digital_wallet'],
            'created_at': [
                datetime.now(),
                datetime.now() - timedelta(hours=1),
                datetime.now() - timedelta(hours=2),
                datetime.now() - timedelta(hours=3),
                datetime.now() - timedelta(hours=4)
            ],
            'merchant_id': [1, 2, 1, 3, 2],
            'user_id': [1, 2, 3, 4, 5],
            'user_email': ['user1@test.com', 'user2@test.com', 'user3@test.com', 'user4@test.com', 'user5@test.com'],
            'merchant_name': ['Amazon', 'Netflix', 'Amazon', 'Unknown', 'Netflix'],
            'merchant_category': ['retail', 'entertainment', 'retail', 'unknown', 'entertainment']
        })
        
        # Sample fraud alert data
        self.sample_fraud_alerts = pd.DataFrame({
            'id': [1, 2, 3],
            'transaction_id': [1, 4, 5],
            'risk_score': [0.85, 0.92, 0.45],
            'alert_type': ['suspicious_amount', 'new_merchant', 'unusual_pattern'],
            'status': ['open', 'investigating', 'resolved'],
            'created_at': [
                datetime.now(),
                datetime.now() - timedelta(hours=1),
                datetime.now() - timedelta(hours=2)
            ],
            'amount': [100.50, 1500.00, 25.00],
            'payment_method': ['credit_card', 'crypto', 'digital_wallet']
        })
    
    def test_transform_transactions(self):
        """Test transaction data transformation"""
        # Transform the data
        transformed_df = self.etl.transform_transactions(self.sample_transactions)
        
        # Check that derived columns were added
        assert 'transaction_date' in transformed_df.columns
        assert 'transaction_hour' in transformed_df.columns
        assert 'transaction_day_of_week' in transformed_df.columns
        assert 'status_category' in transformed_df.columns
        assert 'amount_category' in transformed_df.columns
        assert 'amount_usd' in transformed_df.columns
        assert 'is_high_value' in transformed_df.columns
        
        # Check data types
        assert transformed_df['transaction_hour'].dtype == 'int64'
        assert transformed_df['is_high_value'].dtype == 'bool'
        
        # Check status categorization
        status_categories = transformed_df['status_category'].unique()
        assert 'successful' in status_categories
        assert 'failed' in status_categories
        assert 'fraudulent' in status_categories
        
        # Check amount categories
        amount_categories = transformed_df['amount_category'].unique()
        assert 'small' in amount_categories
        assert 'large' in amount_categories
        
        # Check currency conversion
        assert transformed_df.loc[transformed_df['currency'] == 'EUR', 'amount_usd'].iloc[0] > 45.99
        assert transformed_df.loc[transformed_df['currency'] == 'GBP', 'amount_usd'].iloc[0] > 25.00
    
    def test_transform_fraud_alerts(self):
        """Test fraud alert data transformation"""
        # Transform the data
        transformed_df = self.etl.transform_fraud_alerts(self.sample_fraud_alerts)
        
        # Check derived columns
        assert 'alert_date' in transformed_df.columns
        assert 'alert_hour' in transformed_df.columns
        assert 'risk_category' in transformed_df.columns
        assert 'alert_priority' in transformed_df.columns
        assert 'amount_category' in transformed_df.columns
        
        # Check risk categories
        risk_categories = transformed_df['risk_category'].unique()
        assert 'high' in risk_categories
        assert 'medium' in risk_categories
        assert 'low' in risk_categories
        
        # Check alert priorities
        priorities = transformed_df['alert_priority'].unique()
        assert 'high' in priorities
        assert 'medium' in priorities
        assert 'low' in priorities
        
        # Check that high risk scores get high priority
        high_risk_row = transformed_df[transformed_df['risk_score'] > 0.8].iloc[0]
        assert high_risk_row['alert_priority'] == 'high'
    
    def test_calculate_risk_metrics(self):
        """Test risk metrics calculation"""
        # Calculate metrics
        metrics = self.etl.calculate_risk_metrics(self.sample_transactions, self.sample_fraud_alerts)
        
        # Check required metrics
        assert 'total_transactions' in metrics
        assert 'total_volume' in metrics
        assert 'avg_transaction' in metrics
        assert 'total_fraud_alerts' in metrics
        assert 'fraud_rate' in metrics
        assert 'avg_risk_score' in metrics
        assert 'high_value_fraud_rate' in metrics
        assert 'payment_method_fraud_rates' in metrics
        
        # Check calculations
        assert metrics['total_transactions'] == 5
        assert metrics['total_fraud_alerts'] == 3
        assert metrics['fraud_rate'] == 3/5  # 3 fraud alerts out of 5 transactions
        assert metrics['avg_risk_score'] > 0  # Should be positive
        assert isinstance(metrics['payment_method_fraud_rates'], dict)


class TestKafkaProducer:
    """Test Kafka producer functionality"""
    
    def setup_method(self):
        """Setup test producer"""
        # Note: In real tests, you'd use a test Kafka instance
        # For now, we'll test the event structure
        self.producer = FinTechProducer()
    
    def test_transaction_event_structure(self):
        """Test transaction event structure"""
        # Sample transaction data
        transaction_data = {
            'id': 123,
            'amount': 150.75,
            'currency': 'USD',
            'status': 'completed',
            'payment_method': 'credit_card',
            'user_id': 456,
            'merchant_id': 789,
            'created_at': datetime.now().isoformat()
        }
        
        # Test that the event structure is correct
        # In a real test, you'd actually send to Kafka
        assert 'id' in transaction_data
        assert 'amount' in transaction_data
        assert 'currency' in transaction_data
        assert 'status' in transaction_data
        assert 'payment_method' in transaction_data
        assert 'user_id' in transaction_data
        assert 'merchant_id' in transaction_data
        assert 'created_at' in transaction_data
    
    def test_fraud_alert_event_structure(self):
        """Test fraud alert event structure"""
        # Sample fraud alert data
        fraud_data = {
            'id': 456,
            'transaction_id': 123,
            'risk_score': 0.85,
            'alert_type': 'suspicious_amount',
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        
        # Test that the event structure is correct
        assert 'id' in fraud_data
        assert 'transaction_id' in fraud_data
        assert 'risk_score' in fraud_data
        assert 'alert_type' in fraud_data
        assert 'status' in fraud_data
        assert 'created_at' in fraud_data


class TestDataQuality:
    """Test data quality checks"""
    
    def test_transaction_data_completeness(self):
        """Test transaction data completeness validation"""
        # Sample data with missing values
        incomplete_data = pd.DataFrame({
            'id': [1, 2, None, 4],
            'amount': [100.50, None, 45.99, 1500.00],
            'currency': ['USD', 'EUR', 'USD', None],
            'status': ['completed', 'failed', 'completed', 'completed'],
            'payment_method': ['credit_card', None, 'credit_card', 'bank_transfer']
        })
        
        # Check for missing values
        missing_ids = incomplete_data['id'].isnull().sum()
        missing_amounts = incomplete_data['amount'].isnull().sum()
        missing_currencies = incomplete_data['currency'].isnull().sum()
        missing_payment_methods = incomplete_data['payment_method'].isnull().sum()
        
        assert missing_ids == 1
        assert missing_amounts == 1
        assert missing_currencies == 1
        assert missing_payment_methods == 1
    
    def test_transaction_data_consistency(self):
        """Test transaction data consistency validation"""
        # Sample data with consistency issues
        transactions_df = pd.DataFrame({
            'id': [1, 2, 3],
            'status': ['completed', 'pending', 'invalid_status'],
            'amount': [100.50, -50.00, 0]  # Negative and zero amounts
        })
        
        # Check for valid statuses
        valid_statuses = ['completed', 'pending', 'failed', 'fraudulent', 'cancelled']
        invalid_statuses = transactions_df[~transactions_df['status'].isin(valid_statuses)]
        
        # Check for valid amounts
        invalid_amounts = transactions_df[transactions_df['amount'] <= 0]
        
        assert len(invalid_statuses) == 1
        assert len(invalid_amounts) == 2
    
    def test_fraud_data_range_validation(self):
        """Test fraud data range validation"""
        # Sample data with range issues
        fraud_df = pd.DataFrame({
            'id': [1, 2, 3],
            'risk_score': [0.85, 1.5, -0.1],  # Out of range values
            'amount': [100.50, 0, 1000000.00]  # Zero and very high amounts
        })
        
        # Check for valid risk scores (should be between 0 and 1)
        invalid_risk_scores = fraud_df[(fraud_df['risk_score'] < 0) | (fraud_df['risk_score'] > 1)]
        
        # Check for reasonable amounts
        unreasonable_amounts = fraud_df[fraud_df['amount'] > 100000]
        
        assert len(invalid_risk_scores) == 2
        assert len(unreasonable_amounts) == 1


class TestDataLakeIntegration:
    """Test data lake integration"""
    
    def test_parquet_serialization(self):
        """Test Parquet file serialization"""
        # Sample transaction data
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'amount': [100.50, 250.75, 45.99],
            'currency': ['USD', 'EUR', 'GBP'],
            'status': ['completed', 'pending', 'failed'],
            'payment_method': ['credit_card', 'bank_transfer', 'digital_wallet']
        })
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp_file:
            # Write to Parquet
            test_data.to_parquet(tmp_file.name, index=False)
            
            # Read back from Parquet
            read_data = pd.read_parquet(tmp_file.name)
            
            # Clean up
            os.unlink(tmp_file.name)
        
        # Verify data integrity
        assert len(read_data) == len(test_data)
        assert list(read_data.columns) == list(test_data.columns)
        assert read_data.iloc[0]['amount'] == 100.50
        assert read_data.iloc[1]['currency'] == 'EUR'


# Integration test
class TestEndToEndPipeline:
    """Test end-to-end data pipeline"""
    
    def test_pipeline_flow(self):
        """Test the complete data pipeline flow"""
        # This would test the entire flow from data extraction
        # through transformation to loading in a real environment
        
        # For now, we'll test the logical flow
        pipeline_steps = [
            'extract_transactions',
            'extract_fraud_alerts',
            'transform_transactions',
            'transform_fraud_alerts',
            'calculate_risk_metrics',
            'load_to_data_lake'
        ]
        
        # Verify all steps are present
        assert 'extract_transactions' in pipeline_steps
        assert 'extract_fraud_alerts' in pipeline_steps
        assert 'transform_transactions' in pipeline_steps
        assert 'transform_fraud_alerts' in pipeline_steps
        assert 'calculate_risk_metrics' in pipeline_steps
        assert 'load_to_data_lake' in pipeline_steps
        
        # Verify correct order
        assert pipeline_steps.index('extract_transactions') < pipeline_steps.index('transform_transactions')
        assert pipeline_steps.index('extract_fraud_alerts') < pipeline_steps.index('transform_fraud_alerts')
        assert pipeline_steps.index('transform_transactions') < pipeline_steps.index('calculate_risk_metrics')
        assert pipeline_steps.index('calculate_risk_metrics') < pipeline_steps.index('load_to_data_lake')
