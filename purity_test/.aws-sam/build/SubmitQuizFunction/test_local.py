import uvicorn
import os
import boto3
from moto import mock_dynamodb
import app

# Patching boto3 to use moto's mock
@mock_dynamodb
def setup_local_database():
    """Creates a mock DynamoDB table for local testing."""
    print("Setting up mock DynamoDB table...")
    
    # Create mock dynamodb table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create table with the same schema as in our CloudFormation
    table = dynamodb.create_table(
        TableName='YalePurityTest',
        KeySchema=[
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    print(f"Table {table.name} created successfully")
    
    # Add some sample data
    table.put_item(
        Item={
            'id': 'test-id-1',
            'timestamp': '2023-08-01T12:00:00',
            'score': 75,
            'demographics': {
                'year': '2024',
                'college': 'Berkeley',
                'gender': 'Male',
                'social_club': 'Sigma Chi'
            },
            'yes_answers': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 99]
        }
    )
    
    table.put_item(
        Item={
            'id': 'test-id-2',
            'timestamp': '2023-08-01T12:30:00',
            'score': 85,
            'demographics': {
                'year': '2023',
                'college': 'Saybrook',
                'gender': 'Female',
                'social_club': None
            },
            'yes_answers': [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 96, 97, 98, 99]
        }
    )
    
    print("Sample data added to table")
    return table

def run_local_api():
    """Run the FastAPI app locally for testing."""
    # Set environment variables needed for the app
    os.environ["TABLE_NAME"] = "YalePurityTest"
    
    # Start the API server
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# Instead of testing locally with mock_dynamodb, for simplicity, let's use DynamoDB Local
if __name__ == "__main__":
    # Set environment variables for the DynamoDB local connection
    os.environ["TABLE_NAME"] = "YalePurityTest" 
    os.environ["DYNAMODB_LOCAL_ENDPOINT"] = "http://localhost:8000"
    os.environ["AWS_REGION"] = "us-east-1"
    
    # Use local credentials to avoid AWS credential lookup
    os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
    
    print("Starting local API server (connecting to DynamoDB local on port 8000)...")
    run_local_api() 