"""
Load testing for FinTech Data Platform API
"""

from locust import HttpUser, task, between
import random
import json

class FintechAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get access token"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.client.post("/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def get_health_check(self):
        """Health check endpoint"""
        self.client.get("/health")
    
    @task(2)
    def get_transactions(self):
        """Get transactions list"""
        if self.token:
            self.client.get("/api/v1/analytics/transactions", headers=self.headers)
        else:
            self.client.get("/api/v1/analytics/transactions")
    
    @task(1)
    def get_fraud_alerts(self):
        """Get fraud alerts"""
        if self.token:
            self.client.get("/api/v1/analytics/fraud-alerts", headers=self.headers)
        else:
            self.client.get("/api/v1/analytics/fraud-alerts")
    
    @task(1)
    def get_analytics_summary(self):
        """Get analytics summary"""
        if self.token:
            self.client.get("/api/v1/analytics/summary", headers=self.headers)
        else:
            self.client.get("/api/v1/analytics/summary")
    
    @task(1)
    def create_transaction(self):
        """Create a new transaction"""
        transaction_data = {
            "time_step": random.randint(1, 100),
            "transaction_type": random.choice(["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]),
            "amount": round(random.uniform(1.0, 10000.0), 2),
            "sender_id": f"C{random.randint(100000000, 999999999)}",
            "sender_old_balance": round(random.uniform(0.0, 50000.0), 2),
            "sender_new_balance": round(random.uniform(0.0, 50000.0), 2),
            "receiver_id": f"M{random.randint(100000000, 999999999)}",
            "receiver_old_balance": round(random.uniform(0.0, 50000.0), 2),
            "receiver_new_balance": round(random.uniform(0.0, 50000.0), 2),
            "is_fraud": random.choice([True, False]),
            "is_flagged_fraud": random.choice([True, False])
        }
        
        if self.token:
            self.client.post(
                "/api/v1/analytics/transactions",
                json=transaction_data,
                headers=self.headers
            )
        else:
            self.client.post("/api/v1/analytics/transactions", json=transaction_data)
