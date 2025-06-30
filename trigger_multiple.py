#!/usr/bin/env python3
import boto3
import json
import time
import concurrent.futures
import argparse

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
    parser = argparse.ArgumentParser(description='Trigger multiple Lambda invocations')
    parser.add_argument('--function-name', type=str, default='voting-automation-voting-function',
                        help='Lambda function name')
    parser.add_argument('--count', type=int, default=15,
                        help='Number of invocations')
    args = parser.parse_args()
    
    print(f"Triggering {args.count} invocations of {args.function_name}")
    
    # Use ThreadPoolExecutor to invoke Lambda functions in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.count) as executor:
        futures = [executor.submit(invoke_lambda, args.function_name) for _ in range(args.count)]
        
        # Wait for all futures to complete
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                status_code = future.result()
                print(f"Invocation {i+1}: Status Code {status_code}")
            except Exception as e:
                print(f"Invocation {i+1}: Error - {e}")
    
    print(f"All {args.count} invocations triggered")

if __name__ == '__main__':
    main()
