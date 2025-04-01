import json
import pytest
import boto3
from moto import mock_dynamodb
from fastapi.testclient import TestClient
import os
import app

client = TestClient(app.app)

@pytest.fixture
def mock_dynamodb_table():
    """Set up mock DynamoDB table for testing."""
    with mock_dynamodb():
        # Create mock dynamodb table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create table with the same schema as in our CloudFormation
        table = dynamodb.create_table(
            TableName="YalePurityTest",
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Set environment variable
        os.environ["TABLE_NAME"] = "YalePurityTest"
        
        # Add some sample data
        table.put_item(
            Item={
                "id": "test-id-1",
                "timestamp": "2023-08-01T12:00:00",
                "score": 75,
                "demographics": {
                    "year": "2024",
                    "college": "Berkeley",
                    "gender": "Male",
                    "social_club": "Sigma Chi"
                },
                "yes_answers": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 99]
            }
        )
        
        yield table


def test_submit_quiz(mock_dynamodb_table):
    """Test quiz submission endpoint."""
    # Create a sample quiz submission
    submission = {
        "demographics": {
            "year": "2025",
            "college": "Timothy Dwight",
            "gender": "Male",
            "social_club": "Delta Kappa Epsilon"
        },
        "answers": {
            "answers": [True, False, True, False, True] + [False] * 95  # 3 "yes" answers
        }
    }
    
    # Submit the quiz
    response = client.post("/submit", json=submission)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 97  # 100 - 3 "yes" answers
    assert "id" in data
    assert "timestamp" in data


def test_get_stats(mock_dynamodb_table):
    """Test getting statistics for a submission."""
    # Get stats for the sample submission
    response = client.get("/stats/test-id-1")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-id-1"
    assert data["score"] == 75
    assert "distribution" in data
    assert "question_stats" in data


def test_get_fun_facts(mock_dynamodb_table):
    """Test getting fun facts."""
    response = client.get("/fun-facts")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "fun_facts" in data
    assert isinstance(data["fun_facts"], list)


def test_submit_invalid_quiz():
    """Test submitting an invalid quiz (missing required fields)."""
    submission = {
        "demographics": {
            "college": "Timothy Dwight",
            # Missing required "year" field
        },
        "answers": {
            "answers": [True, False, True]
        }
    }
    
    # Submit the quiz
    response = client.post("/submit", json=submission)
    
    # Check response
    assert response.status_code == 422  # Validation error


def test_get_nonexistent_stats(mock_dynamodb_table):
    """Test getting stats for a non-existent submission."""
    response = client.get("/stats/nonexistent-id")
    
    # Check response
    assert response.status_code == 404 