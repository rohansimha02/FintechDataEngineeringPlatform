"""
Configuration settings for the FinTech Data Platform
"""

import os
from typing import List

# Application settings
APP_NAME: str = "FinTech Data Platform API"
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
VERSION: str = "1.0.0"

# Database settings
DATABASE_URL: str = "postgresql://fintech_user:fintech_password@localhost:5432/fintech_platform"

# Settings class for compatibility
class settings:
    DATABASE_URL = DATABASE_URL
    DEBUG = DEBUG
    APP_NAME = APP_NAME
    VERSION = VERSION

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
KAFKA_TOPIC_TRANSACTIONS: str = "fintech-transactions"
KAFKA_TOPIC_FRAUD_ALERTS: str = "fintech-fraud-alerts"
KAFKA_GROUP_ID: str = "fintech-platform-group"

# MinIO settings
MINIO_ENDPOINT: str = "localhost:9000"
MINIO_ACCESS_KEY: str = "minioadmin"
MINIO_SECRET_KEY: str = "minioadmin"
MINIO_BUCKET_NAME: str = "fintech-data"
MINIO_SECURE: bool = False

# API settings
API_V1_STR: str = "/api/v1"
ALLOWED_ORIGINS: List[str] = ["*"]

# Security settings
SECRET_KEY: str = "your-secret-key-here"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Logging settings
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "json"

# Airflow settings
AIRFLOW_API_URL: str = "http://localhost:8080"
AIRFLOW_USERNAME: str = "airflow"
AIRFLOW_PASSWORD: str = "airflow"

# Data processing settings
BATCH_SIZE: int = 1000
MAX_WORKERS: int = 4
