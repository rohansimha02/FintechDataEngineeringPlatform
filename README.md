
# Fintech Data Engineering Platform



A data engineering platform that processes millions of financial transactions, implements fraud detection logic, and provides analytics through a dashboard and API. Includes a full SQL schema for real database integration and queries.

## Project Overview


This project demonstrates end-to-end data engineering capabilities using the **PaySim financial transaction dataset** (included in `/data`). The platform showcases data processing, basic fraud detection logic, and interactive analytics via API and dashboard.


### Key Features:
- Data processing pipeline for large transaction datasets
- Fraud detection logic and alerting
- REST API (FastAPI) for analytics and data access
- Interactive dashboard (Dash)
- Modular codebase for easy extension
- SQL schema for transactions, fraud alerts, and users


**Live Dashboard Demo:**

## System Architecture

The platform is organized into modular components:

- **Data**: PaySim CSV dataset (`/data`)
- **ETL Pipeline**: Data extraction, transformation, and loading (`app/pipelines/etl_pipeline.py`)
- **API**: FastAPI REST endpoints for analytics (`app/api/main.py`, `app/api/routers/analytics.py`)
- **Dashboard**: Interactive analytics dashboard (`app/dashboard/main.py`)



### Repository Structure
```
FintechTransactionAnalyticsPlatform/
├── app/
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │       └── analytics.py
│   │     
│   │      
│   │       
│   │      
│   ├── core/
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── fraud_alert.py
│   │   └── schemas.py
│   ├── pipelines/
│   │   └── etl_pipeline.py
│   └── streaming/
│       └── kafka_producer.py
├── data/
│   └── PS_20174392719_1491204439457_log.csv
├── tests/
│   ├── test_api.py
│   └── test_data_engineering.py
├── main.py
├── requirements.txt
├── schema.sql
└── README.md
```


## Quick Start

### Prerequisites
- Python 3.9+
- PaySim dataset (included in `/data`)

### Installation & Setup
```bash
# Clone repository
git clone <repository-url>
cd FintechDataEngineeringPlatform

# Install dependencies
pip install -r requirements.txt

# Run the complete platform (API + Dashboard)
python main.py

# Or run individual components:
# API only:
uvicorn app.api.main:app --reload --port 8000
# Dashboard only:
python app/dashboard/main.py
```


### Access Points
- **Dashboard**: http://localhost:8061
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health


## Core Features & Capabilities

### Data Processing
- Handles millions of transactions from the PaySim dataset
- ETL pipeline for cleaning and transforming data

### Fraud Detection
- Implements fraud detection logic and alerting
- Risk scoring and pattern recognition

### API & Dashboard
- FastAPI REST endpoints for analytics
- Dash-based interactive dashboard

### Testing
- Unit tests for API and ETL pipeline



## Technology Stack

- **Python 3.9+**
- **Pandas & NumPy**
- **FastAPI** (API)
- **Dash & Plotly** (Dashboard)
- **SQLAlchemy** (ORM)
- **Kafka** (Streaming)
- **MinIO** (Object storage)
- **pytest** (Testing)
- **psycopg2** (PostgreSQL driver)
- **structlog** (Logging)



## Database Schema

The project includes a full SQL schema (`schema.sql`) for:
- `transactions`: All PaySim transaction fields
- `fraud_alerts`: Fraud detection events linked to transactions
- `users`: User/account management

You can use these tables for real SQL queries, analytics, and integration with PostgreSQL or other databases.

## Data Analysis

The platform analyzes transaction types, fraud rates, and risk metrics using the PaySim dataset. Key insights and metrics are available via the dashboard, API endpoints, and SQL queries.


## Use Cases

- Data engineering portfolio project
- Financial transaction analytics
- Fraud detection demonstration
- Dashboard and API development


## Development & Testing

### Local Development
```bash
# Clone and setup
git clone <repository-url>
cd FintechDataEngineeringPlatform
pip install -r requirements.txt

# Run the complete platform
python main.py

# Run individual components
python app/dashboard/main.py    # Dashboard only
uvicorn app.api.main:app --reload  # API only

# Run tests
pytest tests/                   # All tests
pytest tests/test_api.py        # API tests only
pytest tests/test_data_engineering.py  # ETL pipeline tests
```

### Code Quality
- Type hints and docstrings throughout
- Unit tests for core modules
- Black formatting and flake8 style recommended


## Skills Demonstrated

- ETL pipeline design for large datasets
- Fraud detection logic and analytics
- REST API and dashboard development
- Modular, maintainable Python code
- Unit testing and code quality practices


## Future Enhancements

- Improved fraud detection models
- More advanced analytics and visualizations
- Additional API endpoints
- Integration with external databases or streaming platforms


## License & Contributing

This project is for educational and portfolio purposes, demonstrating data engineering and analytics skills.

### Contributing
Contributions are welcome! Please submit pull requests or open issues for improvements or new features.

### Acknowledgments
- PaySim Dataset: Realistic financial transaction data for fraud detection research
- Open Source Community: Built with open-source Python libraries

---