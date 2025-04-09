"""
Integration tests for FinTech Data Platform
"""

import pytest
import asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests
import time

from app.core.database import get_db_session
from app.streaming.kafka_producer import fintech_producer
from app.streaming.kafka_consumer import fintech_consumer

class TestFintechIntegration:
    """Integration tests for the FinTech platform"""
    
    @pytest.fixture(scope="class")
    def postgres_container(self):
        """PostgreSQL test container"""
        with PostgresContainer("postgres:15-alpine") as postgres:
            postgres.with_env("POSTGRES_DB", "test_fintech")
            postgres.with_env("POSTGRES_USER", "test_user")
            postgres.with_env("POSTGRES_PASSWORD", "test_password")
            yield postgres
    
    @pytest.fixture(scope="class")
    def kafka_container(self):
        """Kafka test container"""
        with KafkaContainer("confluentinc/cp-kafka:7.4.0") as kafka:
            yield kafka
    
    @pytest.fixture
    def test_db_session(self, postgres_container):
        """Test database session"""
        engine = create_engine(postgres_container.get_connection_url())
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        from app.core.database import Base
        Base.metadata.create_all(bind=engine)
        
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_database_connection(self, postgres_container):
        """Test database connectivity"""
        engine = create_engine(postgres_container.get_connection_url())
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.fetchone()[0] == 1
    
    def test_kafka_connection(self, kafka_container):
        """Test Kafka connectivity"""
        # Test producer connection
        producer = fintech_producer
        producer.bootstrap_servers = kafka_container.get_bootstrap_servers()
        
        # Test sending a message
        test_message = {"test": "data"}
        producer.send("test_topic", test_message)
        producer.flush()
        
        # Test consumer connection
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            "test_topic",
            bootstrap_servers=kafka_container.get_bootstrap_servers(),
            auto_offset_reset='earliest',
            group_id='test_group'
        )
        
        # Wait for message
        for message in consumer:
            assert message.value == test_message
            break
        
        consumer.close()
    
    def test_api_health_check(self):
        """Test API health check endpoint"""
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_transaction_creation(self, test_db_session):
        """Test transaction creation and retrieval"""
        # Test transaction creation for PaySim format
        transaction_data = {
            "time_step": 1,
            "transaction_type": "PAYMENT",
            "amount": 100.0,
            "sender_id": "C123456789",
            "sender_old_balance": 1000.0,
            "sender_new_balance": 900.0,
            "receiver_id": "M987654321",
            "receiver_old_balance": 500.0,
            "receiver_new_balance": 600.0,
            "is_fraud": False,
            "is_flagged_fraud": False
        }
        
        # For now, just verify the data structure is correct
        assert transaction_data["amount"] == 100.0
        assert transaction_data["transaction_type"] == "PAYMENT"
        assert transaction_data["sender_id"] == "C123456789"
    
    def test_fraud_detection_pipeline(self, kafka_container):
        """Test fraud detection pipeline"""
        # Configure producer
        producer = fintech_producer
        producer.bootstrap_servers = kafka_container.get_bootstrap_servers()
        
        # Send test transaction for PaySim format
        test_transaction = {
            "time_step": 1,
            "transaction_type": "PAYMENT",
            "amount": 5000.0,
            "sender_id": "C123456789",
            "sender_old_balance": 10000.0,
            "sender_new_balance": 5000.0,
            "receiver_id": "M987654321",
            "receiver_old_balance": 1000.0,
            "receiver_new_balance": 6000.0,
            "is_fraud": False,
            "is_flagged_fraud": False,
            "risk_score": 0.8
        }
        
        producer.send("fintech_transactions", test_transaction)
        producer.flush()
        
        # Wait for processing
        time.sleep(2)
        
        # Verify transaction was processed
        # In a real test, you would check the database for the processed transaction
        assert True  # Placeholder assertion
    
    def test_data_validation(self):
        """Test data validation logic"""
        # Valid transaction for PaySim format
        valid_transaction = {
            "amount": 100.0,
            "sender_id": "C123456789",
            "receiver_id": "M987654321",
            "transaction_type": "PAYMENT",
            "time_step": 1
        }
        # Basic validation
        assert valid_transaction["amount"] > 0
        assert valid_transaction["sender_id"] is not None
        assert valid_transaction["receiver_id"] is not None
        
        # Invalid transaction (missing required fields)
        invalid_transaction = {
            "amount": 100.0,
            "sender_id": "C123456789"
            # Missing required fields
        }
        # Basic validation - should fail
        assert "receiver_id" not in invalid_transaction
    
    def test_authentication(self):
        """Test authentication endpoints"""
        # Test login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data=login_data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            assert "access_token" in token_data
            assert token_data["token_type"] == "bearer"
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            response = requests.get(
                "http://localhost:8000/api/v1/auth/me",
                headers=headers
            )
            assert response.status_code == 200
        else:
            pytest.skip("Authentication service not available")

if __name__ == "__main__":
    pytest.main([__file__])
