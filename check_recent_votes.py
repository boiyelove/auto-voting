#!/usr/bin/env python3
import boto3
import json
import argparse
from datetime import datetime, timedelta

def list_recent_reports(bucket_name, prefix='reports/', minutes=5):
    """List all reports in the S3 bucket from the last few minutes"""
    s3_client = boto3.client('s3')
    
    # Calculate the cutoff time
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    
    # List objects in the bucket
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix
    )
    
    if 'Contents' not in response:
        print(f"No reports found in {bucket_name}/{prefix}")
        return []
    
    # Filter objects by last modified time
    recent_objects = [obj for obj in response['Contents'] 
                     if obj['LastModified'].replace(tzinfo=None) > cutoff_time]
    
    # Group objects by execution ID
    executions = {}
    for obj in recent_objects:
        key = obj['Key']
        if not key.endswith('.json'):
            continue
        
        parts = key.split('/')[-1].split('_')
        if len(parts) < 2:
            continue
        
        execution_id = parts[0]
        report_type = parts[1].split('.')[0]
        
        if execution_id not in executions:
            executions[execution_id] = {'id': execution_id, 'reports': {}}
        
        executions[execution_id]['reports'][report_type] = key
    
    return executions

def get_report_content(bucket_name, key):
    """Get the content of a report"""
    s3_client = boto3.client('s3')
    
    response = s3_client.get_object(
        Bucket=bucket_name,
        Key=key
    )
    
    content = response['Body'].read().decode('utf-8')
    return json.loads(content)

def main():
    parser = argparse.ArgumentParser(description='Check recent voting attempts')
    parser.add_argument('--bucket', type=str, default='voting-screenshots-102014306014',
                        help='S3 bucket name')
    parser.add_argument('--minutes', type=int, default=5,
                        help='Number of minutes to look back')
    args = parser.parse_args()
    
    executions = list_recent_reports(args.bucket, minutes=args.minutes)
    
    if not executions:
        print(f"No executions found in the last {args.minutes} minutes")
        return
    
    print(f"Found {len(executions)} executions in the last {args.minutes} minutes")
    print()
    
    # Sort executions by timestamp (most recent first)
    sorted_executions = []
    for execution_id, execution in executions.items():
        if 'complete' in execution['reports']:
            complete_report = get_report_content(args.bucket, execution['reports']['complete'])
            execution['timestamp'] = complete_report['timestamp']
            execution['success'] = complete_report['success']
            sorted_executions.append(execution)
    
    sorted_executions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Print execution summary
    print("Execution Summary:")
    print("=================")
    success_count = 0
    for execution in sorted_executions:
        status = "SUCCESS" if execution['success'] else "FAILED"
        if execution['success']:
            success_count += 1
        print(f"{execution['timestamp']} - {execution['id']} - {status}")
    
    print()
    print(f"Success rate: {success_count}/{len(sorted_executions)} ({success_count/len(sorted_executions)*100:.1f}%)")
    
    print()
    print("Latest Execution Details:")
    print("========================")
    if sorted_executions:
        latest = sorted_executions[0]
        
        # Get error report if available
        if 'error' in latest['reports']:
            error_report = get_report_content(args.bucket, latest['reports']['error'])
            print(f"Error: {error_report['message']}")
        
        # Get complete report
        complete_report = get_report_content(args.bucket, latest['reports']['complete'])
        print(f"Status: {complete_report['status']}")
        print(f"Success: {complete_report['success']}")
        print(f"Message: {complete_report['message']}")
    
if __name__ == '__main__':
    main()
