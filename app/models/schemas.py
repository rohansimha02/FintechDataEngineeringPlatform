"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# PaySim Transaction schemas
class TransactionBase(BaseModel):
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrg: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float
    isFraud: bool
    isFlaggedFraud: bool

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    oldbalanceOrg: Optional[float] = None
    newbalanceOrg: Optional[float] = None
    oldbalanceDest: Optional[float] = None
    newbalanceDest: Optional[float] = None
    isFraud: Optional[bool] = None
    isFlaggedFraud: Optional[bool] = None

class TransactionResponse(TransactionBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    size: int

# Fraud Alert schemas
class FraudAlertBase(BaseModel):
    transaction_id: int
    alert_type: str
    severity: str
    description: str
    is_resolved: bool = False

class FraudAlertCreate(FraudAlertBase):
    pass

class FraudAlertUpdate(BaseModel):
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    is_resolved: Optional[bool] = None

class FraudAlertResponse(FraudAlertBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FraudAlertListResponse(BaseModel):
    fraud_alerts: List[FraudAlertResponse]
    total: int
    page: int
    size: int
