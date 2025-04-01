.PHONY: install test run build deploy clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	cd api && pytest test_api.py -v

# Run locally
run:
	cd api && python test_local.py

# Build the SAM application
build:
	sam build

# Deploy to AWS
deploy:
	sam deploy --guided

# Deploy without prompts (for CI/CD)
deploy-ci:
	sam deploy --no-confirm-changeset --no-fail-on-empty-changeset

# Delete the stack
delete:
	sam delete

# Clean build artifacts
clean:
	rm -rf .aws-sam
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Start a new shell with AWS SAM CLI
shell:
	sam local start-api

# Generate a sample event for testing
sample-event:
	@echo '{
	  "demographics": {
	    "year": "2023",
	    "college": "Berkeley",
	    "gender": "Male",
	    "social_club": "Alpha Delta Phi"
	  },
	  "answers": {
	    "answers": [true, false, true, false, true, false, true, false, true, false]
	  }
	}' > event.json
	@echo "Created sample event.json" 