"""
Analytics router for FinTech dashboard and visualizations
Uses PaySim financial transaction data for fraud detection analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta
import json
import os

from app.core.database import get_db
from app.models import FraudAlert

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Get dashboard metrics for PaySim fraud detection visualization"""
    try:
        # Read PaySim data for analytics
        paysim_file = "data/PS_20174392719_1491204439457_log.csv"
        
        if not os.path.exists(paysim_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PaySim data file not found"
            )
        
        # Read sample of data for dashboard (first 10000 rows for performance)
        df = pd.read_csv(paysim_file, nrows=10000)
        
        # Calculate basic metrics
        total_transactions = len(df)
        total_fraud = df['isFraud'].sum()
        fraud_rate = total_fraud / total_transactions if total_transactions > 0 else 0
        
        # Transaction type breakdown
        transaction_types = df['type'].value_counts().to_dict()
        
        # Amount statistics
        avg_amount = df['amount'].mean()
        total_volume = df['amount'].sum()
        
        # Fraud statistics
        fraud_amount = df[df['isFraud'] == 1]['amount'].sum()
        avg_fraud_amount = df[df['isFraud'] == 1]['amount'].mean() if total_fraud > 0 else 0
        
        return {
            "summary": {
                "total_transactions": total_transactions,
                "total_fraud": total_fraud,
                "fraud_rate": round(fraud_rate * 100, 2),
                "total_volume": round(total_volume, 2),
                "avg_amount": round(avg_amount, 2),
                "fraud_amount": round(fraud_amount, 2),
                "avg_fraud_amount": round(avg_fraud_amount, 2)
            },
            "transaction_types": transaction_types
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


@router.get("/transactions")
async def get_transaction_analytics(db: Session = Depends(get_db)):
    """Get PaySim transaction analytics data"""
    try:
        paysim_file = "data/PS_20174392719_1491204439457_log.csv"
        
        if not os.path.exists(paysim_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PaySim data file not found"
            )
        
        # Read sample data for analytics
        df = pd.read_csv(paysim_file, nrows=50000)
        
        # Group by step (time) for time series analysis
        transactions_by_step = df.groupby('step').size().to_dict()
        
        # Transaction type distribution
        type_distribution = df['type'].value_counts().to_dict()
        
        # Amount distribution
        amount_bins = [0, 100, 1000, 10000, float('inf')]
        amount_labels = ['small', 'medium', 'large', 'very_large']
        df['amount_category'] = pd.cut(df['amount'], bins=amount_bins, labels=amount_labels)
        amount_distribution = df['amount_category'].value_counts().to_dict()
        
        return {
            "transactions_by_step": transactions_by_step,
            "type_distribution": type_distribution,
            "amount_distribution": amount_distribution,
            "total_transactions": len(df)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction analytics: {str(e)}"
        )


@router.get("/fraud")
async def get_fraud_analytics(db: Session = Depends(get_db)):
    """Get PaySim fraud analytics data"""
    try:
        paysim_file = "data/PS_20174392719_1491204439457_log.csv"
        
        if not os.path.exists(paysim_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PaySim data file not found"
            )
        
        # Read sample data for fraud analysis
        df = pd.read_csv(paysim_file, nrows=50000)
        
        # Filter fraud transactions
        fraud_df = df[df['isFraud'] == 1]
        
        # Fraud by transaction type
        fraud_by_type = fraud_df['type'].value_counts().to_dict()
        
        # Fraud amount analysis
        fraud_amount_stats = {
            "total_fraud_amount": fraud_df['amount'].sum(),
            "avg_fraud_amount": fraud_df['amount'].mean(),
            "max_fraud_amount": fraud_df['amount'].max(),
            "min_fraud_amount": fraud_df['amount'].min()
        }
        
        # Fraud by step (time pattern)
        fraud_by_step = fraud_df.groupby('step').size().to_dict()
        
        # Flagged vs actual fraud
        flagged_fraud = df[df['isFlaggedFraud'] == 1]
        fraud_stats = {
            "total_fraud": len(fraud_df),
            "flagged_fraud": len(flagged_fraud),
            "detection_rate": len(flagged_fraud) / len(fraud_df) if len(fraud_df) > 0 else 0
        }
        
        return {
            "fraud_by_type": fraud_by_type,
            "fraud_amount_stats": fraud_amount_stats,
            "fraud_by_step": fraud_by_step,
            "fraud_statistics": fraud_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fraud analytics: {str(e)}"
        )


@router.get("/visualization")
async def get_visualization_data(db: Session = Depends(get_db)):
    """Get data formatted for visualization libraries"""
    try:
        # Get dashboard metrics
        dashboard = await get_dashboard_metrics(db)
        
        # Get transaction analytics
        transactions = await get_transaction_analytics(db)
        
        # Get fraud analytics
        fraud = await get_fraud_analytics(db)
        
        return {
            "dashboard": dashboard,
            "transactions": transactions,
            "fraud": fraud,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get visualization data: {str(e)}"
        )
