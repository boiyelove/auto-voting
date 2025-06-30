#!/bin/bash

# Create a deployment package for AWS Lambda

# Create a directory for the package
mkdir -p lambda_package

# Install required packages to the package directory
pip install selenium boto3 chromedriver-binary -t lambda_package/

# Download headless Chromium for Lambda
cd lambda_package
curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-55/stable-headless-chromium-amazonlinux-2.zip > headless-chromium.zip
unzip headless-chromium.zip
rm headless-chromium.zip

# Copy the Lambda function code
cp ../lambda_function.py .

# Create the deployment package
zip -r ../lambda_deployment_package.zip .

# Clean up
cd ..
echo "Deployment package created: lambda_deployment_package.zip"
