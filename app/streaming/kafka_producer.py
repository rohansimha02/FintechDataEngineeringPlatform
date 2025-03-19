"""
Kafka Producer for FinTech Data Platform
Handles real-time event streaming for transactions and fraud alerts
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception

from app.core.config import settings

logger = logging.getLogger(__name__)


class FinTechProducer:
    """Kafka producer for FinTech events"""
    
    def __init__(self):
        """Initialize Kafka producer"""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available - using mock producer")
            self.producer = None
            return
            
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def send_transaction_event(self, transaction_data: Dict[str, Any]) -> bool:
        """Send transaction event to Kafka"""
        if not self.producer:
            logger.info("Mock: Transaction event would be sent to Kafka")
            return True
            
        try:
            event = {
                "event_type": "transaction_created",
                "timestamp": datetime.now().isoformat(),
                "data": transaction_data
            }
            
            # Send to transactions topic
            future = self.producer.send(
                'fintech-transactions',
                value=event,
                key=str(transaction_data.get('id', 'unknown'))
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Transaction event sent successfully",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                transaction_id=transaction_data.get('id')
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send transaction event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending transaction event: {e}")
            return False
    
    def send_fraud_alert_event(self, fraud_data: Dict[str, Any]) -> bool:
        """Send fraud alert event to Kafka"""
        if not self.producer:
            logger.info("Mock: Fraud alert event would be sent to Kafka")
            return True
            
        try:
            event = {
                "event_type": "fraud_alert_created",
                "timestamp": datetime.now().isoformat(),
                "data": fraud_data
            }
            
            # Send to fraud alerts topic
            future = self.producer.send(
                'fintech-fraud-alerts',
                value=event,
                key=str(fraud_data.get('id', 'unknown'))
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Fraud alert event sent successfully",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                alert_id=fraud_data.get('id')
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send fraud alert event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending fraud alert event: {e}")
            return False
    
    def send_user_event(self, user_data: Dict[str, Any], event_type: str = "user_updated") -> bool:
        """Send user event to Kafka"""
        try:
            event = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": user_data
            }
            
            # Send to users topic
            future = self.producer.send(
                'fintech-users',
                value=event,
                key=str(user_data.get('id', 'unknown'))
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"User event sent successfully",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                user_id=user_data.get('id'),
                event_type=event_type
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send user event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending user event: {e}")
            return False
    
    def send_merchant_event(self, merchant_data: Dict[str, Any], event_type: str = "merchant_updated") -> bool:
        """Send merchant event to Kafka"""
        try:
            event = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": merchant_data
            }
            
            # Send to merchants topic
            future = self.producer.send(
                'fintech-merchants',
                value=event,
                key=str(merchant_data.get('id', 'unknown'))
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Merchant event sent successfully",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                merchant_id=merchant_data.get('id'),
                event_type=event_type
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send merchant event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending merchant event: {e}")
            return False
    
    def send_risk_score_event(self, risk_data: Dict[str, Any]) -> bool:
        """Send risk score event to Kafka"""
        try:
            event = {
                "event_type": "risk_score_updated",
                "timestamp": datetime.now().isoformat(),
                "data": risk_data
            }
            
            # Send to risk scores topic
            future = self.producer.send(
                'fintech-risk-scores',
                value=event,
                key=str(risk_data.get('user_id', 'unknown'))
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Risk score event sent successfully",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                user_id=risk_data.get('user_id')
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send risk score event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending risk score event: {e}")
            return False
    
    def send_compliance_event(self, compliance_data: Dict[str, Any]) -> bool:
        """Send compliance event to Kafka"""
        try:
            event = {
                "event_type": "compliance_report_generated",
                "timestamp": datetime.now().isoformat(),
                "data": compliance_data
            }
            
            # Send to compliance topic
            future = self.producer.send(
                'fintech-compliance',
                value=event,
                key=str(compliance_data.get('id', 'unknown'))
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Compliance event sent successfully",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                report_id=compliance_data.get('id')
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send compliance event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending compliance event: {e}")
            return False
    
    def close(self):
        """Close the Kafka producer"""
        if not self.producer:
            logger.info("Mock Kafka producer closed")
            return
            
        try:
            self.producer.close()
            logger.info("Kafka producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")


# Global producer instance
fintech_producer = FinTechProducer()
