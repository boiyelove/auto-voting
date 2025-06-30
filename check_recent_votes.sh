#!/bin/bash

# Get the current timestamp in seconds
current_time=$(date +%s)

# Calculate the timestamp for 10 minutes ago
ten_minutes_ago=$((current_time - 600))

# Format the timestamp for AWS CLI
formatted_time=$(date -r $ten_minutes_ago -u +"%Y-%m-%dT%H:%M:%SZ")

echo "Checking for reports since $formatted_time"
echo

# List all complete reports in the S3 bucket
echo "Recent complete reports:"
echo "======================="
aws s3 ls s3://voting-screenshots-102014306014/reports/ --recursive | grep "_complete.json" | sort -r | head -n 20

echo
echo "Checking CloudWatch logs for successful votes:"
echo "============================================="
aws logs filter-log-events --log-group-name /aws/lambda/voting-automation-voting-function --start-time $((ten_minutes_ago * 1000)) --filter-pattern "Vote successful" | grep "Vote successful"

echo
echo "Checking CloudWatch logs for website accessibility:"
echo "=================================================="
aws logs filter-log-events --log-group-name /aws/lambda/voting-automation-voting-function --start-time $((ten_minutes_ago * 1000)) --filter-pattern "Website is not accessible" | grep "Website is not accessible" | head -n 5
