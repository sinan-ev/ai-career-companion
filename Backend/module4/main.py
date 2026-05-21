"""
Main entry point for Module 4.

This script initializes and runs the FastAPI application for the Decision Intelligence Engine.
"""

import uvicorn
from api.routes_4 import app

if __name__ == "__main__":
    uvicorn.run("api.routes_4:app", host="0.0.0.0", port=8004, reload=True)

