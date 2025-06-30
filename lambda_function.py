import json
import os
import logging
import random
import time
import uuid
import boto3
from datetime import datetime
import socket
import urllib.request
import urllib.parse
import urllib.error
import re

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set a shorter timeout for urllib
socket.setdefaulttimeout(3)

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
        
        # Record the execution
        execution_id = str(uuid.uuid4())[:8]
        logger.info(f"Execution ID: {execution_id}")
        
        # Save a status report to S3
        status_report = {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'started',
            'message': 'Vote automation started'
        }
        save_json_to_s3(status_report, s3_bucket, f'reports/{execution_id}_start.json')
        
        # Check if the website is accessible
        website_status = check_website_status("https://democracyheroesaward.com/iconic-senator-of-the-year/")
        if website_status != 200:
            logger.warning(f"Website is not accessible: {website_status}")
            
            # Save error report
            error_report = {
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'message': f'Website is not accessible: {website_status}'
            }
            save_json_to_s3(error_report, s3_bucket, f'reports/{execution_id}_error.json')
            
            # Save completion report
            completion_report = {
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'success': False,
                'message': 'Website is not accessible'
            }
            save_json_to_s3(completion_report, s3_bucket, f'reports/{execution_id}_complete.json')
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'execution_id': execution_id,
                    'success': False,
                    'message': f'Website is not accessible: {website_status}',
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Attempt to vote using urllib with retries
        success = False
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} of {max_retries}")
                success = vote_with_urllib(s3_bucket, execution_id)
                if success:
                    break
                time.sleep(1)  # Wait 1 second between attempts
            except urllib.error.HTTPError as e:
                if e.code == 503:
                    logger.warning(f"Received 503 error on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        logger.info("Retrying...")
                        time.sleep(1)
                else:
                    logger.error(f"HTTP error {e.code} on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        # Save error report
                        error_report = {
                            'execution_id': execution_id,
                            'timestamp': datetime.now().isoformat(),
                            'status': 'error',
                            'message': f'HTTP error {e.code}'
                        }
                        save_json_to_s3(error_report, s3_bucket, f'reports/{execution_id}_error.json')
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    # Save error report
                    error_report = {
                        'execution_id': execution_id,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'error',
                        'message': str(e)
                    }
                    save_json_to_s3(error_report, s3_bucket, f'reports/{execution_id}_error.json')
        
        # Save completion report
        completion_report = {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'success': success,
            'message': 'Vote automation completed'
        }
        save_json_to_s3(completion_report, s3_bucket, f'reports/{execution_id}_complete.json')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'execution_id': execution_id,
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

def check_website_status(url, timeout=3):
    """Check if a website is accessible"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.getcode()
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)

def save_to_s3(content, bucket_name, file_name):
    """Save content to S3 bucket"""
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Body=content,
            Bucket=bucket_name,
            Key=file_name
        )
        logger.info(f"Content saved to S3: {file_name}")
    except Exception as e:
        logger.error(f"Error saving to S3: {e}")

def save_json_to_s3(data, bucket_name, file_name):
    """Save JSON data to S3 bucket"""
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Body=json.dumps(data),
            Bucket=bucket_name,
            Key=file_name,
            ContentType='application/json'
        )
        logger.info(f"JSON saved to S3: {file_name}")
    except Exception as e:
        logger.error(f"Error saving JSON to S3: {e}")

def vote_with_urllib(s3_bucket, execution_id):
    """Attempt to vote using urllib"""
    run_id = str(uuid.uuid4())[:8]  # Generate a unique ID for this run
    
    try:
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
        
        # Create a request with headers
        req = urllib.request.Request(url, headers=headers)
        
        # Open the URL and read the response
        with urllib.request.urlopen(req) as response:
            html = response.read()
            
        # Save the initial page
        save_to_s3(html, s3_bucket, f'screenshots/{execution_id}_{run_id}_initial_page.html')
        
        # Convert bytes to string for regex
        html_str = html.decode('utf-8')
        
        # Check if we're already showing results (already voted)
        if "Thank you for voting" in html_str:
            logger.info(f"Run {run_id}: Already voted")
            return False
        
        # Extract the poll ID and form data
        poll_id_match = re.search(r'name="poll_id" value="(\d+)"', html_str)
        if not poll_id_match:
            logger.error(f"Run {run_id}: Could not find poll ID")
            return False
        
        poll_id = poll_id_match.group(1)
        logger.info(f"Run {run_id}: Found poll ID: {poll_id}")
        
        # Find all available options
        option_matches = re.findall(r'<input type="radio" id="poll-answer-(\d+)" name="poll_(\d+)" value="(\d+)" />\s*<label for="poll-answer-\d+">([^<]+)</label>', html_str)
        if not option_matches:
            logger.error(f"Run {run_id}: Could not find any voting options")
            return False
        
        # Choose SEN. SANI MUSA as the target candidate
        target_candidate = "SEN. SANI MUSA"
        option_value = None
        
        for match in option_matches:
            if target_candidate in match[3]:
                option_value = match[2]
                logger.info(f"Run {run_id}: Found option value {option_value} for {target_candidate}")
                break
        
        if not option_value:
            # If target candidate not found, choose a random option
            random_option = random.choice(option_matches)
            option_value = random_option[2]
            logger.info(f"Run {run_id}: Target candidate not found, using random option {option_value} for {random_option[3]}")
        
        # Extract the wp-polls nonce
        nonce_match = re.search(r'id="poll_\d+_nonce" name="wp-polls-nonce" value="([^"]+)"', html_str)
        if not nonce_match:
            logger.error(f"Run {run_id}: Could not find nonce")
            return False
        
        nonce = nonce_match.group(1)
        logger.info(f"Run {run_id}: Found nonce: {nonce}")
        
        # Step 2: Submit the vote
        logger.info(f"Run {run_id}: Submitting vote")
        
        # Prepare form data
        form_data = {
            'poll_id': poll_id,
            f'poll_{poll_id}': option_value,
            'wp-polls-nonce': nonce,
            'action': 'polls'
        }
        
        # Add a small delay to mimic human behavior
        time.sleep(random.uniform(0.5, 1))
        
        # Encode the form data
        data = urllib.parse.urlencode(form_data).encode('utf-8')
        
        # Create a request with headers and data
        req = urllib.request.Request(url, data=data, headers=headers)
        
        # Submit the vote
        with urllib.request.urlopen(req) as response:
            vote_response = response.read()
        
        # Save the response
        save_to_s3(vote_response, s3_bucket, f'screenshots/{execution_id}_{run_id}_vote_response.html')
        
        # Convert bytes to string for checking
        vote_response_str = vote_response.decode('utf-8')
        
        # Check if the vote was successful
        if "Thank you for voting" in vote_response_str or "Results" in vote_response_str:
            logger.info(f"Run {run_id}: Vote successful!")
            return True
        else:
            logger.warning(f"Run {run_id}: Vote may not have been successful")
            return False
        
    except Exception as e:
        logger.error(f"Run {run_id}: Error during voting process: {e}")
        raise
