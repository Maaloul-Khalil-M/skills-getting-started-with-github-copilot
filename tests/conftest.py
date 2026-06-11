"""
Pytest configuration and shared fixtures for the FastAPI application tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Fixture providing a TestClient for the FastAPI application.
    Used by all tests to make HTTP requests to the app.
    """
    return TestClient(app)
