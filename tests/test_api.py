"""
API Tests for FinTech Data Platform
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.core.database import get_db, Base
from app.models import FraudAlert

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fintech-data-platform"


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestAnalyticsAPI:
    """Test analytics API endpoints"""
    
    def test_dashboard_metrics(self):
        """Test dashboard metrics endpoint"""
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "transaction_types" in data
    
    def test_transaction_analytics(self):
        """Test transaction analytics endpoint"""
        response = client.get("/api/v1/analytics/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions_by_step" in data
        assert "type_distribution" in data
        assert "amount_distribution" in data
    
    def test_fraud_analytics(self):
        """Test fraud analytics endpoint"""
        response = client.get("/api/v1/analytics/fraud")
        assert response.status_code == 200
        data = response.json()
        assert "fraud_by_type" in data
        assert "fraud_amount_stats" in data
        assert "fraud_statistics" in data
    
    def test_visualization_data(self):
        """Test visualization data endpoint"""
        response = client.get("/api/v1/analytics/visualization")
        assert response.status_code == 200
        data = response.json()
        assert "dashboard" in data
        assert "transactions" in data
        assert "fraud" in data
        assert "timestamp" in data
    

