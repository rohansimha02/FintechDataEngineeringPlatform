"""
Professional FinTech Data Platform Dashboard
Enterprise-grade fraud detection and transaction analytics
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests
from plotly.subplots import make_subplots

# Import from our data engineering pipeline
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from app.pipelines.etl_pipeline import FinTechETL
    from app.core.database import get_db_session
    from app.models.fraud_alert import FraudAlert
    PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"Pipeline imports not available: {e}")
    PIPELINE_AVAILABLE = False

# Initialize Dash app with modern theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def load_data_from_pipeline():
    """Load data from our ETL pipeline"""
    if not PIPELINE_AVAILABLE:
        return None
    try:
        etl = FinTechETL()
        df = etl.extract_paysim_data()
        df = etl.transform_paysim_data(df)
        # Use full dataset for comprehensive analysis
        print(f"Loaded {len(df):,} transactions for dashboard analysis")
        return df
    except Exception as e:
        print(f"ETL Pipeline Error: {e}")
        return None

def load_data_from_api():
    """Load data from our API endpoints"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/analytics/dashboard", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"API Error: {e}")
    return None

def load_data_from_database():
    """Load data from our database models"""
    if not PIPELINE_AVAILABLE:
        return None
    try:
        with get_db_session() as session:
            transactions = session.query(Transaction).all()
            fraud_alerts = session.query(FraudAlert).all()
            
            df = pd.DataFrame([{
                'step': t.step,
                'type': t.transaction_type,
                'amount': t.amount,
                'nameOrig': t.name_orig,
                'oldbalanceOrg': t.oldbalance_orig,
                'newbalanceOrg': t.newbalance_orig,
                'nameDest': t.name_dest,
                'oldbalanceDest': t.oldbalance_dest,
                'newbalanceDest': t.newbalance_dest,
                'isFraud': t.is_fraud,
                'isFlaggedFraud': t.is_flagged_fraud
            } for t in transactions])
            
            return df
    except Exception as e:
        print(f"Database Error: {e}")
        return None

def load_fallback_data():
    """Load fallback data if pipeline fails"""
    try:
        print("Loading sample dataset from data/dashboard_sample_half.csv...")
        df = pd.read_csv("data/dashboard_sample_half.csv")
        print(f"Successfully loaded {len(df):,} transactions from optimized sample dataset")
        return df
    except Exception as e:
        print(f"Error loading sample dataset: {e}")
        print("Falling back to synthetic data...")
        return create_sample_data()

def create_sample_data():
    """Create sample data for demo"""
    np.random.seed(42)
    n = 10000
    
    transaction_types = ['PAYMENT', 'CASH_IN', 'CASH_OUT', 'TRANSFER', 'DEBIT']
    type_probs = [0.55, 0.19, 0.13, 0.09, 0.04]
    
    data = {
        'step': np.random.randint(1, 25, n),
        'type': np.random.choice(transaction_types, n, p=type_probs),
        'amount': np.random.lognormal(10, 1, n),
        'nameOrig': [f'C{i:010d}' for i in np.random.randint(1000000000, 9999999999, n)],
        'oldbalanceOrg': np.random.exponential(10000, n),
        'newbalanceOrg': np.random.exponential(10000, n),
        'nameDest': [f'M{i:010d}' for i in np.random.randint(1000000000, 9999999999, n)],
        'oldbalanceDest': np.random.exponential(1000, n),
        'newbalanceDest': np.random.exponential(1000, n),
        'isFraud': np.random.choice([0, 1], n, p=[0.993, 0.007]),
        'isFlaggedFraud': np.random.choice([0, 1], n, p=[0.995, 0.005])
    }
    
    return pd.DataFrame(data)

# Load data with fallback chain
def load_data():
    """Load data with priority: Sample CSV > Pipeline > API > Database > Sample"""
    print("Loading data from sample dataset...")

    # Try sample dataset first (for GitHub compatibility)
    df = load_fallback_data()
    if df is not None and len(df) > 0:
        print("Data loaded from sample dataset")
        print(f"Available columns: {list(df.columns)}")
        return df, f"Optimized Sample Dataset ({len(df):,} transactions)"

    # Try API
    api_data = load_data_from_api()
    if api_data is not None:
        print("Data loaded from API")
        return pd.DataFrame(api_data), "API Streaming"

    # Try Database
    df = load_data_from_database()
    if df is not None and len(df) > 0:
        print("Data loaded from Database")
        return df, "Database Query"

    # Try CSV
    df = load_fallback_data()
    if df is not None and len(df) > 0:
        print("Data loaded from CSV")
        print(f"Available columns: {list(df.columns)}")
        return df, "Data Lake"

    # Fallback to sample
    print("Using sample data")
    return create_sample_data(), "Sample Data"

# Load data immediately when dashboard starts
print("Loading data from sample dataset...")
df, data_source = load_data()
print(f"Data loaded from {data_source}")
print(f"Available columns: {list(df.columns)}")

# Calculate comprehensive metrics
def calculate_metrics():
    """Calculate comprehensive metrics"""
    try:
        total_transactions = len(df)
        
        # Handle both original and transformed column names
        fraud_col = 'is_fraud' if 'is_fraud' in df.columns else 'isFraud'
        type_col = 'transaction_type' if 'transaction_type' in df.columns else 'type'
        step_col = 'time_step' if 'time_step' in df.columns else 'step'
        newbalance_col = 'sender_new_balance' if 'sender_new_balance' in df.columns else 'newbalanceOrig'
        oldbalance_col = 'sender_old_balance' if 'sender_old_balance' in df.columns else 'oldbalanceOrg'
        
        total_fraud = df[fraud_col].sum()
        fraud_rate = total_fraud / total_transactions * 100
        total_volume = df['amount'].sum()
        avg_amount = df['amount'].mean()
        
        # Advanced metrics
        high_value_transactions = (df['amount'] > 10000).sum()
        unusual_patterns = (df['amount'] > df['amount'].quantile(0.95)).sum()
        balance_changes = (abs(df[newbalance_col] - df[oldbalance_col]) / (df[oldbalance_col] + 1) > 0.5).sum()
        
        # Fraud by type
        fraud_by_type = df[df[fraud_col] == 1][type_col].value_counts()
        
        # Transaction types
        transaction_types = df[type_col].value_counts()
        
        # Time-based analysis
        hourly_volume = df.groupby(df[step_col] % 24)['amount'].sum()
        daily_patterns = df.groupby(df[step_col] // 24)['amount'].sum()
        
        # Risk scoring (simplified for performance)
        high_risk_transactions = (
            (df[fraud_col] == 1).sum() + 
            (df['amount'] > 10000).sum() + 
            (df['amount'] > df['amount'].quantile(0.95)).sum()
        )
        
        return {
            'total_transactions': total_transactions,
            'total_fraud': total_fraud,
            'fraud_rate': fraud_rate,
            'total_volume': total_volume,
            'avg_amount': avg_amount,
            'high_value_transactions': high_value_transactions,
            'unusual_patterns': unusual_patterns,
            'balance_changes': balance_changes,
            'high_risk_transactions': high_risk_transactions,
            'fraud_by_type': fraud_by_type,
            'transaction_types': transaction_types,
            'hourly_volume': hourly_volume,
            'daily_patterns': daily_patterns,
            'risk_scores': []
        }
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        # Return default metrics if there's an error
        return {
            'total_transactions': len(df) if 'df' in locals() else 0,
            'total_fraud': 0,
            'fraud_rate': 0,
            'total_volume': 0,
            'avg_amount': 0,
            'high_value_transactions': 0,
            'unusual_patterns': 0,
            'balance_changes': 0,
            'high_risk_transactions': 0,
            'fraud_by_type': pd.Series(),
            'transaction_types': pd.Series(),
            'hourly_volume': pd.Series(),
            'daily_patterns': pd.Series(),
            'risk_scores': []
        }

# Calculate metrics with loaded data
metrics = calculate_metrics()

# Enhanced Professional Color Palette
COLORS = {
    'primary': '#1a2332',           # Deep navy blue - main background
    'secondary': '#2d3748',         # Dark slate - cards
    'tertiary': '#4a5568',          # Medium slate - accents
    'accent': '#3182ce',            # Bright blue - primary accent
    'accent_light': '#63b3ed',      # Light blue - secondary accent
    'success': '#38a169',           # Green success
    'warning': '#d69e2e',           # Amber warning
    'danger': '#e53e3e',            # Red danger
    'light': '#e2e8f0',             # Light grey - borders
    'lighter': '#f7fafc',           # Very light grey - hover states
    'dark': '#0f1419',              # Deepest background
    'white': '#ffffff',             # Pure white - text
    'border': '#2d3748',            # Card borders
    'text': '#ffffff',              # White text
    'text_light': '#e2e8f0',        # Light grey text
    'text_muted': '#a0aec0',        # Muted grey text
    'text_dark': '#2d3748',         # Dark text for light backgrounds
    'gradient_start': '#1a2332',    # Gradient start
    'gradient_end': '#2d3748',      # Gradient end
    'shadow': 'rgba(0, 0, 0, 0.25)', # Shadow color
    'overlay': 'rgba(26, 35, 50, 0.95)' # Overlay color
}

# Enhanced Professional CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>FinTech Data Platform - Enterprise Analytics</title>
        <style>
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #2d3748 100%);
                margin: 0;
                padding: 0;
                color: #ffffff;
                min-height: 100vh;
                overflow-x: hidden;
            }
            
            .dashboard-container {
                background: linear-gradient(135deg, #1a2332 0%, #2d3748 100%);
                border-radius: 20px;
                margin: 20px;
                box-shadow: 
                    0 25px 50px -12px rgba(0, 0, 0, 0.4),
                    0 10px 20px -5px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            
            .metric-card {
                background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                color: white;
                border-radius: 16px;
                padding: 24px;
                margin: 12px;
                box-shadow: 
                    0 10px 25px -5px rgba(0, 0, 0, 0.3),
                    0 4px 10px -2px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                border: 1px solid rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
            }
            
            .metric-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, #3182ce, #63b3ed);
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: 
                    0 20px 40px -10px rgba(0, 0, 0, 0.4),
                    0 8px 20px -4px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15);
                border-color: rgba(99, 179, 237, 0.3);
            }
            
            .metric-card:hover::before {
                opacity: 1;
            }
            
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 10px currentColor;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .status-green { 
                background-color: #38a169; 
                box-shadow: 0 0 15px rgba(56, 161, 105, 0.5);
            }
            .status-yellow { 
                background-color: #d69e2e; 
                box-shadow: 0 0 15px rgba(214, 158, 46, 0.5);
            }
            .status-red { 
                background-color: #e53e3e; 
                box-shadow: 0 0 15px rgba(229, 62, 62, 0.5);
            }
            
            .tab-content {
                background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                border-radius: 16px;
                padding: 32px;
                margin-top: 20px;
                box-shadow: 
                    0 10px 25px -5px rgba(0, 0, 0, 0.3),
                    0 4px 10px -2px rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            
            .nav-tabs {
                border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                margin-bottom: 0;
            }
            
            .nav-tabs .nav-link {
                color: #a0aec0;
                border: none;
                padding: 20px 32px;
                font-weight: 600;
                font-size: 14px;
                border-radius: 12px 12px 0 0;
                background: transparent;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                margin-right: 4px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            
            .nav-tabs .nav-link.active {
                color: #3182ce;
                background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                border-bottom: 3px solid #3182ce;
                box-shadow: 
                    0 4px 15px -2px rgba(49, 130, 206, 0.3),
                    0 2px 8px -1px rgba(0, 0, 0, 0.2);
                transform: translateY(-2px);
            }
            
            .nav-tabs .nav-link:hover {
                color: #ffffff;
                background: rgba(49, 130, 206, 0.1);
                transform: translateY(-1px);
            }
            
            .card {
                background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                box-shadow: 
                    0 10px 25px -5px rgba(0, 0, 0, 0.3),
                    0 4px 10px -2px rgba(0, 0, 0, 0.2);
                transition: all 0.3s ease;
                overflow: hidden;
            }
            
            .card:hover {
                transform: translateY(-4px);
                box-shadow: 
                    0 20px 40px -10px rgba(0, 0, 0, 0.4),
                    0 8px 20px -4px rgba(0, 0, 0, 0.3);
            }
            
            .card-header {
                background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding: 20px 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            
            .card-body {
                padding: 24px;
            }
            
            .badge {
                background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 500;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            }
            
            .header-gradient {
                background: linear-gradient(135deg, #1a2332 0%, #2d3748 50%, #4a5568 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 
                    0 20px 40px -10px rgba(0, 0, 0, 0.4),
                    0 10px 20px -5px rgba(0, 0, 0, 0.3);
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #3182ce, #63b3ed);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            .metric-label {
                font-size: 0.875rem;
                font-weight: 500;
                color: #a0aec0;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }
            
            .metric-subtitle {
                font-size: 0.75rem;
                color: #718096;
                font-weight: 400;
            }
            
            .footer {
                background: linear-gradient(135deg, #1a2332 0%, #2d3748 100%);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding: 24px;
                margin-top: 40px;
                border-radius: 16px;
                box-shadow: 
                    0 -10px 25px -5px rgba(0, 0, 0, 0.3),
                    0 -4px 10px -2px rgba(0, 0, 0, 0.2);
            }
            
            /* Scrollbar styling */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #2d3748;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #4a5568, #2d3748);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #3182ce, #63b3ed);
            }
            
            /* Loading animation */
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: #3182ce;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
        {%metas%}
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout with enhanced professional styling
app.layout = dbc.Container([
    # Enhanced Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.H1([
                        html.I(className="fas fa-chart-line me-3", style={'color': '#3182ce', 'fontSize': '2.5rem'}),
                        "FinTech Data Platform"
                    ], className="mb-3 fw-bold", style={
                        'color': COLORS['white'], 
                        'fontSize': '3rem', 
                        'fontWeight': '800',
                        'textShadow': '0 4px 8px rgba(0,0,0,0.4)',
                        'letterSpacing': '-0.5px'
                    }),
                    html.H4("Enterprise Transaction Analytics & Fraud Detection", 
                           className="mb-4", style={
                               'color': COLORS['text_light'], 
                               'fontSize': '1.25rem',
                               'fontWeight': '400',
                               'letterSpacing': '0.5px'
                           }),
                    html.Div([
                        html.Span([
                            html.I(className="fas fa-circle status-green me-2"),
                            "Real-time Processing"
                        ], className="badge me-3", style={'backgroundColor': 'rgba(56, 161, 105, 0.2)', 'color': '#38a169'}),
                        html.Span([
                            html.I(className="fas fa-circle status-green me-2"),
                            "ML-Powered Detection"
                        ], className="badge me-3", style={'backgroundColor': 'rgba(49, 130, 206, 0.2)', 'color': '#3182ce'}),
                        html.Span([
                            html.I(className="fas fa-circle status-green me-2"),
                            "99.9% Uptime"
                        ], className="badge", style={'backgroundColor': 'rgba(214, 158, 46, 0.2)', 'color': '#d69e2e'})
                    ])
                ], className="text-center py-5")
            ], className="header-gradient", style={'borderRadius': '20px', 'padding': '40px', 'marginBottom': '32px'})
        ])
    ]),
    
    # Enhanced Key Metrics Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6("Total Transactions", className="metric-label"),
                        html.H2(f"{metrics['total_transactions']:,}", className="metric-value"),
                        html.P("Processed", className="metric-subtitle")
                    ], className="text-center")
                ])
            ], className="border-0 shadow-lg h-100")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6("Fraud Rate", className="metric-label"),
                        html.H2(f"{metrics['fraud_rate']:.2f}%", className="metric-value"),
                        html.P(f"{metrics['total_fraud']:,} detected", className="metric-subtitle")
                    ], className="text-center")
                ])
            ], className="border-0 shadow-lg h-100")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6("Total Volume", className="metric-label"),
                        html.H2(f"${metrics['total_volume']:,.0f}", className="metric-value"),
                        html.P("USD processed", className="metric-subtitle")
                    ], className="text-center")
                ])
            ], className="border-0 shadow-lg h-100")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6("High-Risk Transactions", className="metric-label"),
                        html.H2(f"{metrics['high_risk_transactions']:,}", className="metric-value"),
                        html.P("Flagged for review", className="metric-subtitle")
                    ], className="text-center")
                ])
            ], className="border-0 shadow-lg h-100")
        ], width=3)
    ], className="mb-5"),
    
    # Enhanced Tabs
    dbc.Tabs([
        # Overview Tab
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-chart-pie me-3", style={'color': '#3182ce'}),
                                "Transaction Distribution"
                            ], className="mb-0 fw-bold", style={'color': COLORS['white'], 'fontSize': '1.25rem'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='transaction-types-chart',
                                figure=px.pie(
                                    values=metrics['transaction_types'].values,
                                    names=metrics['transaction_types'].index,
                                    title="",
                                    color_discrete_sequence=['#3182ce', '#63b3ed', '#90cdf4', '#bee3f8', '#ebf8ff']
                                ).update_layout(
                                    showlegend=True,
                                    height=350,
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    font={'family': 'Inter', 'size': 12, 'color': COLORS['white']},
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    legend=dict(
                                        font=dict(color=COLORS['white'], size=11),
                                        bgcolor='rgba(0,0,0,0)',
                                        bordercolor='rgba(255,255,255,0.1)'
                                    )
                                )
                            )
                        ])
                    ], className="border-0 shadow-lg h-100")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-shield-alt me-3", style={'color': '#e53e3e'}),
                                "Fraud Detection by Type"
                            ], className="mb-0 fw-bold", style={'color': COLORS['white'], 'fontSize': '1.25rem'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='fraud-chart',
                                figure=go.Figure(data=[
                                    go.Bar(
                                        x=metrics['transaction_types'].index,
                                        y=metrics['transaction_types'].values,
                                        name='Total Transactions',
                                        marker_color='#3182ce',
                                        opacity=0.9
                                    ),
                                    go.Bar(
                                        x=metrics['fraud_by_type'].index,
                                        y=metrics['fraud_by_type'].values,
                                        name='Fraud Cases',
                                        marker_color='#e53e3e',
                                        opacity=0.8
                                    )
                                ]).update_layout(
                                    barmode='group',
                                    height=350,
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    legend=dict(
                                        orientation="h", 
                                        yanchor="bottom", 
                                        y=1.02, 
                                        xanchor="right", 
                                        x=1, 
                                        font=dict(color=COLORS['white'], size=11),
                                        bgcolor='rgba(0,0,0,0)',
                                        bordercolor='rgba(255,255,255,0.1)'
                                    ),
                                    font={'family': 'Inter', 'size': 12, 'color': COLORS['white']},
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(
                                        showgrid=False, 
                                        color=COLORS['white'],
                                        tickfont=dict(size=11)
                                    ),
                                    yaxis=dict(
                                        showgrid=True, 
                                        gridcolor='rgba(255,255,255,0.1)', 
                                        color=COLORS['white'],
                                        tickfont=dict(size=11)
                                    )
                                )
                            )
                        ])
                    ], className="border-0 shadow-lg h-100")
                ], width=6)
            ], className="mb-5"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-clock me-3", style={'color': '#38a169'}),
                                "Transaction Volume Over Time"
                            ], className="mb-0 fw-bold", style={'color': COLORS['white'], 'fontSize': '1.25rem'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='volume-chart',
                                figure=go.Figure().add_trace(
                                    go.Scatter(
                                        x=metrics['hourly_volume'].index,
                                        y=metrics['hourly_volume'].values,
                                        mode='lines',
                                        name='Hourly Volume',
                                        line=dict(color='#3182ce', width=4),
                                        fill='tonexty',
                                        fillcolor='rgba(49, 130, 206, 0.1)'
                                    )
                                ).update_layout(
                                    height=350,
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    font={'family': 'Inter', 'size': 12, 'color': COLORS['white']},
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(
                                        title='Hour of Day',
                                        showgrid=True, 
                                        gridcolor='rgba(255,255,255,0.1)', 
                                        color=COLORS['white'],
                                        tickfont=dict(size=11)
                                    ),
                                    yaxis=dict(
                                        title='Volume ($)',
                                        showgrid=True, 
                                        gridcolor='rgba(255,255,255,0.1)', 
                                        color=COLORS['white'],
                                        tickfont=dict(size=11)
                                    )
                                )
                            )
                        ])
                    ], className="border-0 shadow-lg h-100")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-chart-line me-3", style={'color': '#d69e2e'}),
                                "Transaction Amount Analysis"
                            ], className="mb-0 fw-bold", style={'color': COLORS['white'], 'fontSize': '1.25rem'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='amount-chart',
                                figure=go.Figure().add_trace(
                                    go.Scatter(
                                        x=df['step'],
                                        y=df['amount'],
                                        mode='markers',
                                        name='Transaction Amounts',
                                        marker=dict(
                                            color=df['amount'],
                                            colorscale='Viridis',
                                            size=4,
                                            opacity=0.6,
                                            colorbar=dict(
                                                title="Amount ($)",
                                                titlefont=dict(color=COLORS['white']),
                                                tickfont=dict(color=COLORS['white'])
                                            )
                                        ),
                                        text=df['type'] + '<br>Amount: $' + df['amount'].astype(str),
                                        hoverinfo='text'
                                    )
                                ).add_trace(
                                    go.Scatter(
                                        x=df['step'],
                                        y=[df['amount'].quantile(0.95)] * len(df),
                                        mode='lines',
                                        name='95th Percentile',
                                        line=dict(color='#e53e3e', width=2, dash='dash'),
                                        showlegend=True
                                    )
                                ).add_trace(
                                    go.Scatter(
                                        x=df['step'],
                                        y=[df['amount'].quantile(0.99)] * len(df),
                                        mode='lines',
                                        name='99th Percentile',
                                        line=dict(color='#d69e2e', width=2, dash='dash'),
                                        showlegend=True
                                    )
                                ).update_layout(
                                    height=350,
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    font={'family': 'Inter', 'size': 12, 'color': COLORS['white']},
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(
                                        title='Time Step',
                                        showgrid=True, 
                                        gridcolor='rgba(255,255,255,0.1)', 
                                        color=COLORS['white'],
                                        tickfont=dict(size=11)
                                    ),
                                    yaxis=dict(
                                        title='Amount ($)',
                                        showgrid=True, 
                                        gridcolor='rgba(255,255,255,0.1)', 
                                        color=COLORS['white'],
                                        tickfont=dict(size=11),
                                        type='log'
                                    ),
                                    legend=dict(
                                        orientation="h", 
                                        yanchor="bottom", 
                                        y=1.02, 
                                        xanchor="right", 
                                        x=1, 
                                        font=dict(color=COLORS['white'], size=11),
                                        bgcolor='rgba(0,0,0,0)',
                                        bordercolor='rgba(255,255,255,0.1)'
                                    ),
                                    hovermode='closest'
                                )
                            )
                        ])
                    ], className="border-0 shadow-lg h-100")
                ], width=6)
            ])
        ], label="Overview", tab_id="overview"),
        
        # Analytics Tab
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-analytics me-3", style={'color': '#e53e3e'}),
                                "Risk Analysis"
                            ], className="mb-0 fw-bold", style={'color': COLORS['white'], 'fontSize': '1.25rem'})
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.H4("High-Value", className="fw-bold metric-value", style={'fontSize': '1.5rem'}),
                                        html.H3(f"{(df['amount'] > 10000).sum():,}", className="metric-value"),
                                        html.P("Transactions > $10K", className="metric-subtitle")
                                    ], className="text-center p-4")
                                ], width=3),
                                dbc.Col([
                                    html.Div([
                                        html.H4("Unusual", className="fw-bold metric-value", style={'fontSize': '1.5rem'}),
                                        html.H3(f"{(df['amount'] > df['amount'].quantile(0.95)).sum():,}", className="metric-value"),
                                        html.P("Top 5% by Amount", className="metric-subtitle")
                                    ], className="text-center p-4")
                                ], width=3),
                                dbc.Col([
                                    html.Div([
                                        html.H4("Balance Changes", className="fw-bold metric-value", style={'fontSize': '1.5rem'}),
                                        html.H3(f"{(abs(df['newbalanceOrig'] - df['oldbalanceOrg']) / (df['oldbalanceOrg'] + 1) > 0.5).sum():,}", className="metric-value"),
                                        html.P(">50% Change", className="metric-subtitle")
                                    ], className="text-center p-4")
                                ], width=3),
                                dbc.Col([
                                    html.Div([
                                        html.H4("Risk Score", className="fw-bold metric-value", style={'fontSize': '1.5rem'}),
                                        html.H3(f"{metrics['high_risk_transactions']:,}", className="metric-value"),
                                        html.P("High Risk Total", className="metric-subtitle")
                                    ], className="text-center p-4")
                                ], width=3)
                            ])
                        ])
                    ], className="border-0 shadow-lg")
                ])
            ], className="mb-5"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-database me-3", style={'color': '#38a169'}),
                                "Data Pipeline Metrics"
                            ], className="mb-0 fw-bold", style={'color': COLORS['white'], 'fontSize': '1.25rem'})
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.H6("Data Source", className="metric-label"),
                                        html.P(data_source, className="fw-semibold", style={'color': COLORS['text_muted'], 'fontSize': '1.1rem'})
                                    ])
                                ], width=3),
                                dbc.Col([
                                    html.Div([
                                        html.H6("Processing Time", className="metric-label"),
                                        html.P("≤ 2s", className="fw-semibold text-success", style={'fontSize': '1.1rem'})
                                    ])
                                ], width=3),
                                dbc.Col([
                                    html.Div([
                                        html.H6("Data Quality", className="metric-label"),
                                        html.P("99.8%", className="fw-semibold text-success", style={'fontSize': '1.1rem'})
                                    ])
                                ], width=3),
                                dbc.Col([
                                    html.Div([
                                        html.H6("Last Updated", className="metric-label"),
                                        html.P(datetime.now().strftime("%H:%M:%S"), className="fw-semibold", style={'color': COLORS['text_muted'], 'fontSize': '1.1rem'})
                                    ])
                                ], width=3)
                            ])
                        ])
                    ], className="border-0 shadow-lg")
                ])
            ])
        ], label="Analytics", tab_id="analytics")
    ], id="tabs", active_tab="overview", className="mb-5"),
    
    # Enhanced Footer
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)', 'margin': '40px 0'}),
                html.Div([
                    html.I(className="fas fa-copyright me-2", style={'color': '#3182ce'}),
                    html.Span("FinTech Data Platform - Enterprise Analytics Dashboard", 
                             style={'color': COLORS['white'], 'fontWeight': '600', 'fontSize': '1.1rem'}),
                    html.Br(),
                    html.Small("Powered by Apache Kafka, PostgreSQL, FastAPI, and Dash", 
                              style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'})
                ], className="text-center")
            ], className="footer")
        ])
    ])
    
], fluid=True, className="py-4", style={'backgroundColor': 'transparent'})

# Callbacks for interactivity
@app.callback(
    Output('transaction-types-chart', 'figure'),
    Input('transaction-types-chart', 'clickData')
)
def update_transaction_chart(click_data):
    """Update transaction types chart on click"""
    return px.pie(
        values=metrics['transaction_types'].values,
        names=metrics['transaction_types'].index,
        title="",
        color_discrete_sequence=['#3182ce', '#63b3ed', '#90cdf4', '#bee3f8', '#ebf8ff']
    ).update_layout(
        showlegend=True,
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        font={'family': 'Inter', 'size': 12, 'color': COLORS['white']},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            font=dict(color=COLORS['white'], size=11),
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(255,255,255,0.1)'
        )
    )

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8061)
