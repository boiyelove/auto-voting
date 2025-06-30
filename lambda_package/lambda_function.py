import json
import os
import logging
import random
import time
import uuid
import boto3
import requests
from datetime import datetime

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Lambda handler function"""
    try:
        # Get S3 bucket from environment variable
        s3_bucket = os.environ.get('SCREENSHOT_BUCKET')
        if not s3_bucket:
            raise ValueError("SCREENSHOT_BUCKET environment variable not set")
        
        # Log Lambda execution details
        logger.info(f"Lambda function invoked with remaining time: {context.get_remaining_time_in_millis()} ms")
        logger.info(f"Memory limit: {context.memory_limit_in_mb} MB")
        
        # Attempt to vote using requests
        success = vote_with_requests(s3_bucket)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def save_to_s3(content, bucket_name, file_name):
    """Save content to S3 bucket"""
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Body=content,
            Bucket=bucket_name,
            Key=f'screenshots/{file_name}'
        )
        logger.info(f"Content saved to S3: {file_name}")
    except Exception as e:
        logger.error(f"Error saving to S3: {e}")

def vote_with_requests(s3_bucket):
    """Attempt to vote using requests library"""
    run_id = str(uuid.uuid4())[:8]  # Generate a unique ID for this run
    
    try:
        # Set up session to maintain cookies
        session = requests.Session()
        
        # Set up headers to mimic a browser
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://democracyheroesaward.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Step 1: Visit the voting page to get cookies and form data
        logger.info(f"Run {run_id}: Opening website")
        url = "https://democracyheroesaward.com/iconic-senator-of-the-year/"
        response = session.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Run {run_id}: Failed to load page, status code: {response.status_code}")
            save_to_s3(response.content, s3_bucket, f'{run_id}_error_page.html')
            return False
        
        # Save the initial page
        save_to_s3(response.content, s3_bucket, f'{run_id}_initial_page.html')
        
        # Check if we're already showing results (already voted)
        if "Thank you for voting" in response.text or "Results" in response.text or "View Results" in response.text:
            logger.info(f"Run {run_id}: Already voted or showing results")
            return False
        
        # Extract the poll ID and form data
        import re
        poll_id_match = re.search(r'name="poll_id" value="(\d+)"', response.text)
        if not poll_id_match:
            logger.error(f"Run {run_id}: Could not find poll ID")
            return False
        
        poll_id = poll_id_match.group(1)
        logger.info(f"Run {run_id}: Found poll ID: {poll_id}")
        
        # Find the option value for the candidate we want to vote for (option 4)
        option_match = re.search(r'<input type="radio" id="poll-answer-(\d+)" name="poll_(\d+)" value="(\d+)"[^>]*>.*?Senator Shehu Sani', response.text, re.DOTALL)
        if not option_match:
            logger.error(f"Run {run_id}: Could not find option for Senator Shehu Sani")
            return False
        
        option_value = option_match.group(3)
        logger.info(f"Run {run_id}: Found option value: {option_value}")
        
        # Extract the wp-polls nonce
        nonce_match = re.search(r'name="_wpnonce" value="([^"]+)"', response.text)
        if not nonce_match:
            logger.error(f"Run {run_id}: Could not find nonce")
            return False
        
        nonce = nonce_match.group(1)
        
        # Step 2: Submit the vote
        logger.info(f"Run {run_id}: Submitting vote")
        
        # Prepare form data
        form_data = {
            'poll_id': poll_id,
            f'poll_{poll_id}': option_value,
            '_wpnonce': nonce,
            'action': 'polls'
        }
        
        # Add a small delay to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        # Submit the vote
        vote_response = session.post(url, data=form_data, headers=headers, allow_redirects=True)
        
        # Save the response
        save_to_s3(vote_response.content, s3_bucket, f'{run_id}_vote_response.html')
        
        # Check if the vote was successful
        if "Thank you for voting" in vote_response.text or "Results" in vote_response.text:
            logger.info(f"Run {run_id}: Vote successful!")
            return True
        else:
            logger.warning(f"Run {run_id}: Vote may not have been successful")
            return False
        
    except Exception as e:
        logger.error(f"Run {run_id}: Error during voting process: {e}")
        return False
