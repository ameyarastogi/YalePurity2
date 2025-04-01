import os
import json
import boto3
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from aws_lambda_powertools import Logger
from mangum import Mangum

# Initialize logger
logger = Logger(service="purity-test-api")

# Initialize the FastAPI app
app = FastAPI(title="Yale Purity Test API")

# Get DynamoDB table name from environment variable
TABLE_NAME = os.environ.get("TABLE_NAME", "YalePurityTest")

# Initialize DynamoDB client
# Check if we should use a local DynamoDB endpoint
dynamodb_endpoint = os.environ.get("DYNAMODB_LOCAL_ENDPOINT")
if dynamodb_endpoint:
    dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_endpoint)
    logger.info(f"Using local DynamoDB endpoint: {dynamodb_endpoint}")
else:
    dynamodb = boto3.resource("dynamodb")
    logger.info("Using AWS DynamoDB")

table = dynamodb.Table(TABLE_NAME)

# Define the models
class QuizAnswers(BaseModel):
    """Model for the quiz answers."""
    answers: List[bool] = Field(..., description="List of boolean answers (true=yes) for each question")

class Demographics(BaseModel):
    """Model for the demographic information."""
    year: str = Field(..., description="Class year (e.g., 2023, 2024)")
    college: Optional[str] = Field(None, description="Residential college")
    gender: Optional[str] = Field(None, description="Gender")
    social_club: Optional[str] = Field(None, description="Social club or fraternity/sorority")

class QuizSubmission(BaseModel):
    """Model for a quiz submission."""
    demographics: Demographics
    answers: QuizAnswers

class QuizResult(BaseModel):
    """Model for the quiz result."""
    id: str
    score: int
    timestamp: str
    percentile: Optional[float] = None
    distribution: Optional[Dict[str, int]] = None
    question_stats: Optional[Dict[str, float]] = None

@app.post("/submit", response_model=QuizResult)
def submit_quiz(submission: QuizSubmission):
    """
    Submit a quiz and get results.
    
    This endpoint:
    1. Computes the purity score
    2. Stores the submission in DynamoDB
    3. Returns the score and related statistics
    """
    try:
        # Generate a unique ID
        submission_id = str(uuid.uuid4())
        
        # Compute the purity score (100 - number of "yes" answers)
        yes_count = sum(submission.answers.answers)
        score = 100 - yes_count
        
        # Current timestamp
        timestamp = datetime.now().isoformat()
        
        # Prepare the item for DynamoDB
        item = {
            "id": submission_id,
            "timestamp": timestamp,
            "score": score,
            "demographics": {
                "year": submission.demographics.year,
                "college": submission.demographics.college,
                "gender": submission.demographics.gender,
                "social_club": submission.demographics.social_club
            },
            # Store answers as list of indices where the answer was "yes"
            "yes_answers": [i for i, ans in enumerate(submission.answers.answers) if ans]
        }
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        # Calculate basic statistics (we'll compute more in the GetStats function)
        result = QuizResult(
            id=submission_id,
            score=score,
            timestamp=timestamp
        )
        
        return result
    
    except Exception as e:
        logger.exception("Error processing quiz submission")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/{submission_id}", response_model=QuizResult)
def get_stats(submission_id: str):
    """
    Get detailed statistics for a submission.
    
    This endpoint:
    1. Retrieves the submission from DynamoDB
    2. Computes percentile and distribution
    3. Calculates question statistics
    """
    try:
        # Get the submission from DynamoDB
        response = table.get_item(Key={"id": submission_id})
        
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        item = response["Item"]
        
        # Get all scores to calculate percentile and distribution
        scan_response = table.scan(
            ProjectionExpression="score"
        )
        scores = [int(item["score"]) for item in scan_response.get("Items", [])]
        
        # Calculate percentile
        score = item["score"]
        percentile = sum(1 for s in scores if s < score) / len(scores) * 100 if scores else 0
        
        # Calculate score distribution (group scores into buckets)
        distribution = {}
        for s in scores:
            bucket = f"{(s // 10) * 10}-{(s // 10) * 10 + 9}"
            distribution[bucket] = distribution.get(bucket, 0) + 1
        
        # Calculate question statistics (percentage of "yes" for each question)
        all_submissions_scan = table.scan()
        all_submissions = all_submissions_scan.get("Items", [])
        
        question_stats = {}
        total_submissions = len(all_submissions)
        
        # Count "yes" answers for each question
        for q_idx in range(100):  # assuming 100 questions
            yes_count = sum(1 for sub in all_submissions if q_idx in sub.get("yes_answers", []))
            question_stats[str(q_idx)] = yes_count / total_submissions * 100 if total_submissions > 0 else 0
        
        # Construct result
        result = QuizResult(
            id=submission_id,
            score=score,
            timestamp=item["timestamp"],
            percentile=percentile,
            distribution=distribution,
            question_stats=question_stats
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving statistics for submission {submission_id}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fun-facts")
def get_fun_facts():
    """
    Get fun facts from the data.
    
    This endpoint:
    1. Analyzes submissions to find interesting patterns
    2. Returns a list of fun facts
    """
    try:
        # Scan all submissions
        scan_response = table.scan()
        submissions = scan_response.get("Items", [])
        
        if not submissions:
            return {"fun_facts": ["Not enough data to generate fun facts yet."]}
        
        facts = []
        
        # Calculate overall average score
        avg_score = sum(int(sub["score"]) for sub in submissions) / len(submissions)
        facts.append(f"The average purity score is {avg_score:.1f}.")
        
        # Find interesting demographic patterns
        # Example: Compare different colleges
        college_data = {}
        for sub in submissions:
            college = sub.get("demographics", {}).get("college")
            if college:
                if college not in college_data:
                    college_data[college] = {"count": 0, "score_sum": 0}
                college_data[college]["count"] += 1
                college_data[college]["score_sum"] += sub["score"]
        
        # Find colleges with significant differences
        for college, data in college_data.items():
            if data["count"] >= 5:  # Only consider colleges with enough data
                avg = data["score_sum"] / data["count"]
                if abs(avg - avg_score) > 5:  # If significantly different
                    facts.append(f"{college} students average {avg:.1f} on the purity scale.")
        
        # Example: Find interesting question-based facts
        for q_idx in range(100):  # assuming 100 questions
            # Count overall "yes" percentage
            yes_count = sum(1 for sub in submissions if q_idx in sub.get("yes_answers", []))
            yes_percent = yes_count / len(submissions) * 100
            
            # If it's an interesting threshold
            if 20 <= yes_percent <= 30 or 70 <= yes_percent <= 80:
                facts.append(f"{yes_percent:.0f}% of students answered yes to question #{q_idx+1}.")
        
        # Return a few fun facts (limit to avoid overwhelming)
        return {"fun_facts": facts[:5]}
    
    except Exception as e:
        logger.exception("Error generating fun facts")
        raise HTTPException(status_code=500, detail=str(e))

# Lambda handlers
def submit_handler(event, context):
    """AWS Lambda handler for the submit endpoint."""
    # Add CORS headers for preflight OPTIONS requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': ''
        }
    
    # Normal request handling
    asgi_handler = Mangum(app, lifespan="off")
    response = asgi_handler(event, context)
    
    # Add CORS headers to the response
    if 'headers' not in response:
        response['headers'] = {}
    
    response['headers']['Access-Control-Allow-Origin'] = '*'
    response['headers']['Access-Control-Allow-Headers'] = 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    response['headers']['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    
    return response

def stats_handler(event, context):
    """AWS Lambda handler for the stats endpoint."""
    # Add CORS headers for preflight OPTIONS requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': ''
        }
    
    # Normal request handling
    asgi_handler = Mangum(app, lifespan="off")
    response = asgi_handler(event, context)
    
    # Add CORS headers to the response
    if 'headers' not in response:
        response['headers'] = {}
    
    response['headers']['Access-Control-Allow-Origin'] = '*'
    response['headers']['Access-Control-Allow-Headers'] = 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    response['headers']['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    
    return response 