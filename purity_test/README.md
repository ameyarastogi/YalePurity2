# Yale Purity Test

A serverless web application that allows users to take the Yale Purity Test, see their score, and view anonymous statistical aggregations of all submissions. Built using AWS serverless services for maximum scalability and minimum cost.

## Architecture


### Components

1. **Frontend**:
   - Amazon S3 bucket for static content (HTML, CSS, JS)
   - CloudFront distribution for global content delivery and HTTPS

2. **Backend**:
   - API Gateway for HTTP API endpoints
   - Lambda functions for serverless processing
   - DynamoDB for persistent storage of quiz submissions

3. **API Services**:
   - Submit quiz endpoint
   - Get statistics endpoint
   - Fun facts endpoint

## Deployment Details

### Backend Deployment

The backend is deployed using AWS SAM (Serverless Application Model). The deployed resources include:

| Resource | Description | ARN/ID |
|----------|-------------|--------|
| DynamoDB Table | Stores quiz submissions | YalePurityTest |
| Lambda Functions | Process API requests | yale-purity-test-SubmitQuizFunction, yale-purity-test-GetStatsFunction |
| API Gateway | HTTP API endpoints | https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/ |

### Frontend Deployment

The static frontend is deployed to:

- **S3 Bucket**: yale-purity-test-frontend-788279300027
- **CloudFront URL**: https://d356y4wr4fpgvd.cloudfront.net

## API Documentation

The API is built using FastAPI and exposed through AWS API Gateway. All API endpoints support CORS to allow cross-origin requests from the CloudFront domain.

### Base URLs

- **Production**: `https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod`
- **Local Development**: `http://localhost:8000` (when running local server)

### Authentication

The API does not currently require authentication. All endpoints are publicly accessible.

### Endpoints

#### 1. Submit Quiz (`POST /submit`)

Submits a quiz submission with answers and demographic information.

**Request Body**:

```json
{
  "demographics": {
    "year": "2023",           // Required: Class year (e.g., 2023, 2024)
    "college": "Berkeley",    // Optional: Residential college
    "gender": "Male",         // Optional: Gender
    "social_club": "Alpha Delta Phi"  // Optional: Social club or fraternity/sorority
  },
  "answers": {
    "answers": [true, false, true, false, ...]  // Array of 100 boolean values (true = yes, false = no)
  }
}
```

**Response**:

```json
{
  "id": "c4dd25cd-48ae-4710-aeb4-e57e6fe074f9",  // Unique submission ID
  "score": 95,                                   // Purity score (100 - number of "yes" answers)
  "timestamp": "2025-04-01T15:16:24.031112"      // Submission timestamp (ISO format)
}
```

**cURL Example**:
```bash
curl -X POST "https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "demographics": {
      "year": "2023",
      "college": "Berkeley",
      "gender": "Male",
      "social_club": "Alpha Delta Phi"
    },
    "answers": {
      "answers": [true, false, true, false, true, false, true, false, true, false]
    }
  }'
```

**JavaScript Example**:
```javascript
const response = await fetch('https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    demographics: {
      year: '2023',
      college: 'Berkeley',
      gender: 'Male',
      social_club: 'Alpha Delta Phi'
    },
    answers: {
      answers: [true, false, true, false, true, false, true, false, true, false]
    }
  })
});

const result = await response.json();
console.log(result);
```

#### 2. Get Statistics (`GET /stats/{submission_id}`)

Retrieves detailed statistics for a submission, including percentile, score distribution, and per-question statistics.

**Path Parameters**:
- `submission_id` (string, required): The unique ID of the submission to retrieve statistics for.

**Response**:

```json
{
  "id": "c4dd25cd-48ae-4710-aeb4-e57e6fe074f9",  // Submission ID
  "score": 95,                                   // Purity score
  "timestamp": "2025-04-01T15:16:24.031112",     // Submission timestamp
  "percentile": 75.5,                            // Percentile rank among all submissions
  "distribution": {                              // Distribution of scores
    "0-9": 0,
    "10-19": 2,
    "20-29": 5,
    "30-39": 10,
    "40-49": 15,
    "50-59": 20,
    "60-69": 25,
    "70-79": 30,
    "80-89": 35,
    "90-99": 40
  },
  "question_stats": {                           // Percentage of "yes" answers for each question
    "0": 45.5,
    "1": 32.1,
    // ... (for all questions)
    "99": 12.3
  }
}
```

**cURL Example**:
```bash
curl -X GET "https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/stats/c4dd25cd-48ae-4710-aeb4-e57e6fe074f9"
```

**JavaScript Example**:
```javascript
const response = await fetch('https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/stats/c4dd25cd-48ae-4710-aeb4-e57e6fe074f9');
const stats = await response.json();
console.log(stats);
```

#### 3. Get Fun Facts (`GET /fun-facts`)

Retrieves interesting facts derived from the submitted data.

**Response**:

```json
{
  "fun_facts": [
    "The average purity score is 67.8.",
    "Berkeley students average 59.2 on the purity scale.",
    "75% of students answered yes to question #42.",
    "Only 25% of students admitted to having cheated on a test.",
    "Sig Nu brothers have the lowest average purity score at 54.3."
  ]
}
```

**cURL Example**:
```bash
curl -X GET "https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/fun-facts"
```

**JavaScript Example**:
```javascript
const response = await fetch('https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod/fun-facts');
const facts = await response.json();
console.log(facts.fun_facts);
```

### Error Handling

All API endpoints return appropriate HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid input (e.g., missing required fields)
- **404 Not Found**: Resource not found (e.g., submission ID doesn't exist)
- **500 Internal Server Error**: Server-side error

Error responses have the following format:
```json
{
  "detail": "Error message"
}
```

### CORS

The API supports Cross-Origin Resource Sharing (CORS) to allow requests from the frontend domain:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET,POST,OPTIONS`
- `Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept`

## Local Development

### Prerequisites

- Python 3.9+
- AWS SAM CLI
- Docker (for local DynamoDB)
- AWS CLI (configured with credentials)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/YalePurity2.git
   cd YalePurity2
   ```

2. Install dependencies:
   ```bash
   cd purity_test
   pip install -r requirements.txt
   ```

3. Run local DynamoDB:
   ```bash
   docker run -p 8000:8000 amazon/dynamodb-local
   ```

4. Create the table in local DynamoDB:
   ```bash
   aws dynamodb create-table \
     --table-name YalePurityTest \
     --attribute-definitions AttributeName=id,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --endpoint-url http://localhost:8000
   ```

5. Run the local API server:
   ```bash
   cd api
   DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000 TABLE_NAME=YalePurityTest python test_local.py
   ```

6. In a separate terminal, test the local API:
   ```bash
   curl -X POST "http://localhost:8000/submit" \
     -H "Content-Type: application/json" \
     -d '{
       "demographics": {
         "year": "2023",
         "college": "Berkeley",
         "gender": "Male"
       },
       "answers": {
         "answers": [true, false, true, false, true, false, true, false, true, false]
       }
     }'
   ```

### Testing with SAM Local

You can also use SAM local to test the Lambda functions:

```bash
cd purity_test
sam local start-api --env-vars env.json
```

Create an `env.json` file with:
```json
{
  "SubmitQuizFunction": {
    "TABLE_NAME": "YalePurityTest",
    "DYNAMODB_LOCAL_ENDPOINT": "http://localhost:8000"
  },
  "GetStatsFunction": {
    "TABLE_NAME": "YalePurityTest",
    "DYNAMODB_LOCAL_ENDPOINT": "http://localhost:8000"
  }
}
```

## Deploying Changes

### Backend Changes

1. Update code in `purity_test/api/` or the SAM template (`purity_test/template.yaml`)
2. Build and deploy:
   ```bash
   cd purity_test
   sam build
   sam deploy --s3-bucket yale-purity-test-deployment-1743520432 --stack-name yale-purity-test --region us-east-1 --capabilities CAPABILITY_IAM
   ```

### Frontend Changes

1. Update files in `purity_test/frontend/`
2. Sync to S3:
   ```bash
   aws s3 sync purity_test/frontend/ s3://yale-purity-test-frontend-788279300027/ --delete
   ```

3. Invalidate CloudFront cache (optional):
   ```bash
   aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
   ```

## Troubleshooting

### Common Issues

1. **CORS Errors**: If you see CORS errors in the browser console, check:
   - API Gateway CORS configuration
   - Lambda handler CORS headers
   - Browser's cached responses (use Ctrl+Shift+R to force refresh)

2. **DynamoDB Local Connection Errors**:
   - Ensure Docker is running
   - Check the endpoint URL and port (8000)
   - Verify the table has been created successfully

3. **AWS Deployment Failures**:
   - Check CloudFormation events: `aws cloudformation describe-stack-events --stack-name yale-purity-test`
   - Verify IAM permissions
   - Check S3 bucket permissions

### Logs

- **Lambda Logs**: View in CloudWatch Logs
  ```bash
  aws logs get-log-events --log-group-name /aws/lambda/yale-purity-test-SubmitQuizFunction --log-stream-name <LOG_STREAM>
  ```

- **API Gateway Logs**: Enable in API Gateway settings

## Data Model

### DynamoDB Schema

```
YalePurityTest (Table)
└── id (String, Partition Key)
    ├── timestamp (String): ISO timestamp
    ├── score (Number): Purity score (0-100)
    ├── demographics (Map)
    │   ├── year (String): Class year
    │   ├── college (String, Optional): Residential college
    │   ├── gender (String, Optional): Gender
    │   └── social_club (String, Optional): Social club
    └── yes_answers (List of Numbers): Indices of "yes" answers
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name - Initial work 