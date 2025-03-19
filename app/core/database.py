"""
Database configuration for FinTech Data Platform
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    try:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database not available - using mock session: {e}")
        # Return a mock session that doesn't do anything
        class MockSession:
            def query(self, model):
                return MockQuery()
            def add(self, obj):
                pass
            def commit(self):
                pass
            def refresh(self, obj):
                pass
            def close(self):
                pass
        
        class MockQuery:
            def filter(self, *args):
                return self
            def first(self):
                return None
            def all(self):
                return []
            def count(self):
                return 0
            def offset(self, skip):
                return self
            def limit(self, limit):
                return self
        
        yield MockSession()


async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered with Base
        from app.models.user import User
        from app.models.transaction import Transaction
        from app.models.merchant import Merchant
        from app.models.fraud_alert import FraudAlert
        from app.models.risk_score import RiskScore
        from app.models.compliance_report import ComplianceReport
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.warning(f"Database not available - using mock mode: {e}")
        logger.info("API will run without database functionality")


def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
