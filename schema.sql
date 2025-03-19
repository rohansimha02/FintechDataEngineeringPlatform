-- Table for fraud alerts
CREATE TABLE fraud_alerts (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    risk_score NUMERIC(4,3) NOT NULL,
    alert_type VARCHAR(32) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Table for users (accounts)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    email VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Table for transactions
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    step INTEGER NOT NULL,                
    type VARCHAR(20) NOT NULL,            
    amount NUMERIC(18,2) NOT NULL,        
    nameOrig VARCHAR(32) NOT NULL,        
    oldbalanceOrg NUMERIC(18,2) NOT NULL, 
    newbalanceOrg NUMERIC(18,2) NOT NULL, 
    nameDest VARCHAR(32) NOT NULL,        
    oldbalanceDest NUMERIC(18,2) NOT NULL,
    newbalanceDest NUMERIC(18,2) NOT NULL,
    isFraud BOOLEAN NOT NULL,
    isFlaggedFraud BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
