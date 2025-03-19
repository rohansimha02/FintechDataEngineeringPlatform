"""
Fraud Alert model for FinTech Data Platform
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

from app.core.database import Base


class AlertType(str, enum.Enum):
    """Fraud alert type enumeration"""
    SUSPICIOUS_AMOUNT = "suspicious_amount"
    NEW_MERCHANT = "new_merchant"
    UNUSUAL_PATTERN = "unusual_pattern"
    HIGH_RISK_LOCATION = "high_risk_location"
    VELOCITY_CHECK = "velocity_check"
    DEVICE_MISMATCH = "device_mismatch"


class AlertStatus(str, enum.Enum):
    """Fraud alert status enumeration"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    CONFIRMED_FRAUD = "confirmed_fraud"


class FraudAlert(Base):
    """Fraud Alert model for fraud detection"""
    __tablename__ = "fraud_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0.0 to 1.0
    alert_type = Column(Enum(AlertType), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transaction = relationship("Transaction")


# Pydantic models for API
class FraudAlertBase(BaseModel):
    transaction_id: int
    risk_score: float
    alert_type: AlertType
    description: Optional[str] = None


class FraudAlertCreate(FraudAlertBase):
    pass


class FraudAlertUpdate(BaseModel):
    risk_score: Optional[float] = None
    alert_type: Optional[AlertType] = None
    status: Optional[AlertStatus] = None
    description: Optional[str] = None


class FraudAlertResponse(FraudAlertBase):
    id: int
    status: AlertStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FraudAlertListResponse(BaseModel):
    fraud_alerts: list[FraudAlertResponse]
    total: int
    page: int
    size: int
