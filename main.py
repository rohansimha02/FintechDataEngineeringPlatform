#!/usr/bin/env python3
"""
FinTech Data Platform - Main Entry Point
Enterprise-grade data engineering project with real-time analytics
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    """Main entry point for the FinTech Data Platform"""
    print("Starting FinTech Data Platform...")
    print("=" * 50)
    
    # Check if data file exists
    data_file = Path("data/PS_20174392719_1491204439457_log.csv")
    if not data_file.exists():
        print("Error: PaySim data file not found!")
        print("Please ensure the data file is in the data/ directory")
        return
    
    print("Data file found")
    print("Starting API server...")
    
    # Start the FastAPI server in background
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])
    
    # Wait for API to start
    time.sleep(3)
    print("API server started on http://localhost:8000")
    
    print("Starting dashboard...")
    
    # Start the dashboard
    dashboard_process = subprocess.Popen([
        sys.executable, "app/dashboard/main.py"
    ])
    
    print("Dashboard started on http://localhost:8061")
    print("=" * 50)
    print("FinTech Data Platform is running!")
    print("Dashboard: http://localhost:8061")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 50)
    print("Press Ctrl+C to stop all services")
    
    try:
        # Keep the main process running
        api_process.wait()
        dashboard_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down FinTech Data Platform...")
        api_process.terminate()
        dashboard_process.terminate()
        print("All services stopped")

if __name__ == "__main__":
    main()
