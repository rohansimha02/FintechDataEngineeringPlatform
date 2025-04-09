"""
Kafka Consumer for FinTech Data Platform
Handles transaction processing with validation, deduplication, and metrics
"""

import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from kafka import KafkaConsumer
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from prometheus_client import Counter, Histogram, Gauge

from app.core.database import get_db_session
from app.core.config import settings
# Data validator not available for PaySim format
# TransactionCreate not needed for PaySim format

logger = structlog.get_logger()

# Prometheus metrics
TRANSACTION_PROCESSED = Counter(
    'fintech_transactions_processed_total',
    'Total number of transactions processed',
    ['status']
)

TRANSACTION_PROCESSING_TIME = Histogram(
    'fintech_transaction_processing_seconds',
    'Time spent processing transactions'
)

CONSUMER_LAG = Gauge(
    'fintech_consumer_lag',
    'Consumer lag in messages',
    ['topic', 'partition']
)

class FintechKafkaConsumer:
    """Kafka consumer for processing financial transactions"""
    
    def __init__(self):
        self.consumer = None
        self.running = False
        self.processed_ids = set()  # Simple in-memory deduplication
        
    def start(self):
        """Start the Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_TRANSACTIONS,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id='fintech_consumer_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None
            )
            
            self.running = True
            logger.info("Kafka consumer started", topic=settings.KAFKA_TOPIC_TRANSACTIONS)
            
            for message in self.consumer:
                if not self.running:
                    break
                    
                self._process_message(message)
                
        except Exception as e:
            logger.error("Error in Kafka consumer", error=str(e))
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped")
    
    def _process_message(self, message):
        """Process a single Kafka message"""
        start_time = time.time()
        
        try:
            # Extract message data
            transaction_data = message.value
            message_key = message.key or str(uuid.uuid4())
            
            # Check for duplicates
            if message_key in self.processed_ids:
                logger.warning("Duplicate message detected", message_key=message_key)
                TRANSACTION_PROCESSED.labels(status='duplicate').inc()
                return
            
            # Basic validation for PaySim data
            required_fields = ['time_step', 'transaction_type', 'amount', 'sender_id', 'receiver_id']
            if not all(field in transaction_data for field in required_fields):
                logger.error("Invalid transaction data - missing required fields", data=transaction_data)
                TRANSACTION_PROCESSED.labels(status='invalid').inc()
                return
            
            # Process transaction
            self._upsert_transaction(transaction_data, message_key)
            
            # Mark as processed
            self.processed_ids.add(message_key)
            
            # Update metrics
            processing_time = time.time() - start_time
            TRANSACTION_PROCESSING_TIME.observe(processing_time)
            TRANSACTION_PROCESSED.labels(status='success').inc()
            
            # Update lag metrics
            for topic_partition in self.consumer.assignment():
                lag = self.consumer.end_offsets([topic_partition])[topic_partition] - message.offset
                CONSUMER_LAG.labels(
                    topic=topic_partition.topic,
                    partition=topic_partition.partition
                ).set(lag)
            
            logger.info(
                "Transaction processed successfully",
                message_key=message_key,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error("Error processing message", error=str(e), message=message.value)
            TRANSACTION_PROCESSED.labels(status='error').inc()
    
    def _upsert_transaction(self, transaction_data: Dict[str, Any], message_key: str):
        """Upsert transaction to database using ON CONFLICT"""
        with get_db_session() as session:
            try:
                # Prepare transaction data for PaySim format
                transaction_data_processed = {
                    'time_step': transaction_data.get('time_step', 0),
                    'transaction_type': transaction_data.get('transaction_type', 'PAYMENT'),
                    'amount': transaction_data.get('amount', 0.0),
                    'sender_id': transaction_data.get('sender_id', 'C123456789'),
                    'sender_old_balance': transaction_data.get('sender_old_balance', 0.0),
                    'sender_new_balance': transaction_data.get('sender_new_balance', 0.0),
                    'receiver_id': transaction_data.get('receiver_id', 'M123456789'),
                    'receiver_old_balance': transaction_data.get('receiver_old_balance', 0.0),
                    'receiver_new_balance': transaction_data.get('receiver_new_balance', 0.0),
                    'is_fraud': transaction_data.get('is_fraud', False),
                    'is_flagged_fraud': transaction_data.get('is_flagged_fraud', False),
                    'risk_score': transaction_data.get('risk_score', 0.0)
                }
                
                # Upsert using raw SQL for PaySim format
                upsert_query = text("""
                    INSERT INTO transactions (
                        time_step, transaction_type, amount, sender_id, 
                        sender_old_balance, sender_new_balance, receiver_id,
                        receiver_old_balance, receiver_new_balance, is_fraud,
                        is_flagged_fraud, risk_score, created_at, updated_at
                    ) VALUES (
                        :time_step, :transaction_type, :amount, :sender_id,
                        :sender_old_balance, :sender_new_balance, :receiver_id,
                        :receiver_old_balance, :receiver_new_balance, :is_fraud,
                        :is_flagged_fraud, :risk_score, NOW(), NOW()
                    )
                    ON CONFLICT (time_step, sender_id, receiver_id) 
                    DO UPDATE SET
                        amount = EXCLUDED.amount,
                        transaction_type = EXCLUDED.transaction_type,
                        sender_old_balance = EXCLUDED.sender_old_balance,
                        sender_new_balance = EXCLUDED.sender_new_balance,
                        receiver_old_balance = EXCLUDED.receiver_old_balance,
                        receiver_new_balance = EXCLUDED.receiver_new_balance,
                        is_fraud = EXCLUDED.is_fraud,
                        is_flagged_fraud = EXCLUDED.is_flagged_fraud,
                        risk_score = EXCLUDED.risk_score,
                        updated_at = NOW()
                """)
                
                session.execute(upsert_query, transaction_data_processed)
                
                session.commit()
                
            except IntegrityError as e:
                session.rollback()
                logger.error("Database integrity error", error=str(e))
                raise
            except Exception as e:
                session.rollback()
                logger.error("Database error", error=str(e))
                raise

# Global consumer instance
fintech_consumer = FintechKafkaConsumer()
