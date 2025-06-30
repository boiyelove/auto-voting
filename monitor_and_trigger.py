#!/usr/bin/env python3
import requests
import time
import argparse
import boto3
import json
from datetime import datetime

def check_website(url, timeout=5):
    """Check if a website is accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code, response.elapsed.total_seconds()
    except requests.exceptions.Timeout:
        return 'Timeout', timeout
    except requests.exceptions.RequestException as e:
        return f'Error: {e}', timeout

def invoke_lambda(function_name):
    """Invoke a Lambda function"""
    lambda_client = boto3.client('lambda')
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',  # Asynchronous invocation
        Payload=json.dumps({})
    )
    
    return response['StatusCode']

def main():
    parser = argparse.ArgumentParser(description='Monitor website and trigger Lambda function')
    parser.add_argument('--url', type=str, default='https://democracyheroesaward.com/iconic-senator-of-the-year/',
                        help='URL to check')
    parser.add_argument('--timeout', type=int, default=5,
                        help='Timeout in seconds')
    parser.add_argument('--interval', type=int, default=300,
                        help='Interval between checks in seconds')
    parser.add_argument('--function-name', type=str, default='voting-automation-voting-function',
                        help='Lambda function name')
    args = parser.parse_args()
    
    print(f"Monitoring {args.url} with timeout {args.timeout}s, interval {args.interval}s")
    print(f"Will trigger Lambda function {args.function_name} when website is accessible")
    print()
    
    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status, elapsed = check_website(args.url, args.timeout)
        print(f"{timestamp} - Status: {status}, Elapsed: {elapsed:.2f}s")
        
        if status == 200:
            print(f"{timestamp} - Website is accessible, triggering Lambda function")
            try:
                status_code = invoke_lambda(args.function_name)
                print(f"{timestamp} - Lambda function triggered with status code {status_code}")
            except Exception as e:
                print(f"{timestamp} - Error triggering Lambda function: {e}")
        
        time.sleep(args.interval)

if __name__ == '__main__':
    main()
