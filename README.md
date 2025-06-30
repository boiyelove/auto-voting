# Auto Voting

This directory contains scripts and utilities for automating voting on websites that use WordPress Polls.

## Files

### Core Scripts
- `vote_automation.py`: Selenium script for local voting automation
- `lambda_function.py`: AWS Lambda function for vote automation
- `check_voting_status.py`: Script to check the status of voting attempts
- `check_website.py`: Script to check if the website is accessible
- `monitor_and_trigger.py`: Script to monitor the website and trigger the Lambda function when accessible
- `trigger_multiple.py`: Script to trigger multiple Lambda invocations simultaneously

### Deployment Files
- `lambda_deployment_package.zip`: Deployment package for the Lambda function
- `create_selenium_layer.sh`: Script to create Lambda layer with Selenium and Chrome
- `selenium_layer.zip`: Lambda layer with Selenium and Chrome
- `deploy.sh`: Script to deploy AWS resources
- `run_votes.sh`: Script to run the voting automation locally

### CloudFormation Templates
- `bucket-stack.yaml`: CloudFormation template for S3 bucket creation
- `voting-stack.yaml`: CloudFormation template for Lambda function and related resources

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install boto3 requests selenium
   ```

2. Configure AWS credentials:
   ```bash
   aws configure
   ```

## Configuration

The scripts are designed to be configurable. You need to set the following parameters:

- `VOTING_URL`: The URL of the voting page
- `TARGET_CANDIDATE`: The name of the candidate to vote for

These can be set as environment variables for the Lambda function or passed as command-line arguments to the local scripts.

## Usage

### Local Voting Automation

```bash
source venv/bin/activate
python vote_automation.py --url "https://example.com/voting-page/" --candidate "CANDIDATE NAME" --attempts 5
```

Options:
- `--url`: URL of the voting page
- `--candidate`: Name of the candidate to vote for
- `--attempts`: Number of voting attempts (default: 5)
- `--retries`: Maximum retries per attempt (default: 2)
- `--proxy`: Use proxy servers (default: True)
- `--no-proxy`: Do not use proxy servers
- `--incognito`: Use incognito mode (default: True)
- `--no-incognito`: Do not use incognito mode

### Check Website Accessibility

```bash
source venv/bin/activate
python check_website.py --url "https://example.com/voting-page/" --timeout 10 --interval 5 --count 3
```

Options:
- `--url`: URL to check
- `--timeout`: Timeout in seconds (default: 5)
- `--interval`: Interval between checks in seconds (default: 60)
- `--count`: Number of checks to perform (default: 5)

### Check Voting Status

```bash
source venv/bin/activate
python check_voting_status.py --bucket "your-bucket-name" --hours 24
```

Options:
- `--bucket`: S3 bucket name
- `--hours`: Number of hours to look back (default: 24)

### Monitor Website and Trigger Lambda

```bash
source venv/bin/activate
python monitor_and_trigger.py --url "https://example.com/voting-page/" --interval 300 --function-name "your-lambda-function"
```

Options:
- `--url`: URL to check
- `--timeout`: Timeout in seconds (default: 5)
- `--interval`: Interval between checks in seconds (default: 300)
- `--function-name`: Lambda function name

### Trigger Multiple Lambda Invocations

```bash
source venv/bin/activate
python trigger_multiple.py --function-name "your-lambda-function" --count 15
```

Options:
- `--function-name`: Lambda function name
- `--count`: Number of invocations (default: 15)

## Deployment

1. Update the CloudFormation templates with your configuration:
   - Edit `bucket-stack.yaml` to set your bucket name
   - Edit `voting-stack.yaml` to set your voting URL and target candidate

2. Create the S3 bucket:
   ```bash
   aws cloudformation deploy --template-file bucket-stack.yaml --stack-name voting-bucket-stack
   ```

3. Create the Selenium layer:
   ```bash
   ./create_selenium_layer.sh
   ```

4. Deploy the Lambda function and related resources:
   ```bash
   ./deploy.sh
   ```

## AWS Resources

The auto voting system uses the following AWS resources:

- Lambda function
- CloudWatch Event rule
- S3 bucket
- IAM role for Lambda execution

## Lambda Function

The Lambda function performs the following steps:

1. Checks if the website is accessible
2. If accessible, opens the voting page
3. Finds the option for the target candidate
4. Submits the vote
5. Saves screenshots and logs to S3

## Troubleshooting

If the website is not accessible, the Lambda function will log an error and exit. The website's accessibility can be checked using the `check_website.py` script.

Common issues:
- Website timeouts: The website may be down or experiencing technical issues
- Vote already submitted: The website may only allow one vote per IP address
- Element not found: The website structure may have changed

## Notes

- The website may be experiencing technical issues or may be down
- The Lambda function will continue to attempt to vote according to the schedule
- The `monitor_and_trigger.py` script can be used to trigger the Lambda function when the website becomes accessible
