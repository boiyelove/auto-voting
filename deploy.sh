#!/bin/bash

# Set variables
STACK_NAME="voting-automation"
REGION="us-east-1"  # Change to your preferred region

echo "Starting deployment process..."

# Create the Selenium layer
echo "Creating Selenium layer..."
chmod +x create_selenium_layer.sh
./create_selenium_layer.sh

if [ ! -f "selenium_layer.zip" ]; then
    echo "Failed to create selenium_layer.zip"
    exit 1
fi

# Create Lambda deployment package
echo "Creating Lambda deployment package..."
zip -r lambda_deployment_package.zip lambda_function.py

if [ ! -f "lambda_deployment_package.zip" ]; then
    echo "Failed to create lambda_deployment_package.zip"
    exit 1
fi

# First, create the S3 bucket stack
echo "Creating S3 bucket stack..."
aws cloudformation deploy \
  --template-file bucket-stack.yaml \
  --stack-name "${STACK_NAME}-bucket" \
  --capabilities CAPABILITY_IAM \
  --region $REGION

if [ $? -ne 0 ]; then
    echo "Failed to create S3 bucket stack"
    exit 1
fi

# Get the S3 bucket name
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}-bucket" \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --output text \
  --region $REGION)

if [ -z "$S3_BUCKET" ]; then
    echo "Failed to get S3 bucket name"
    exit 1
fi

echo "S3 bucket name: $S3_BUCKET"

# Upload files to S3
echo "Uploading files to S3..."
aws s3 cp selenium_layer.zip "s3://$S3_BUCKET/"
aws s3 cp lambda_deployment_package.zip "s3://$S3_BUCKET/"

if [ $? -ne 0 ]; then
    echo "Failed to upload files to S3"
    exit 1
fi

# Now deploy the main stack
echo "Deploying main stack..."
aws cloudformation deploy \
  --template-file voting-stack.yaml \
  --stack-name "${STACK_NAME}" \
  --capabilities CAPABILITY_IAM \
  --region $REGION

if [ $? -ne 0 ]; then
    echo "Failed to deploy main stack"
    exit 1
fi

# Get the Lambda function name
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
  --output text \
  --region $REGION)

if [ -z "$FUNCTION_NAME" ]; then
    echo "Failed to get Lambda function name"
    exit 1
fi

echo "Deployment completed successfully!"
echo "Lambda function: $FUNCTION_NAME"
echo "S3 bucket: $S3_BUCKET"

# Test the function
echo "Testing the Lambda function..."
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  --region $REGION \
  response.json

if [ $? -eq 0 ]; then
    echo "Lambda function test completed. Check response.json for details."
    cat response.json
else
    echo "Lambda function test failed"
fi
