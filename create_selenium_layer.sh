#!/bin/bash

# Create directories for the layer
mkdir -p selenium-layer/python
mkdir -p selenium-layer/bin

# Install Selenium and its dependencies
pip install selenium requests boto3 urllib3 -t selenium-layer/python/

# Download Chrome and ChromeDriver for AWS Lambda
echo "Downloading Chrome and ChromeDriver for AWS Lambda..."
mkdir -p temp_downloads

# Download headless Chromium
echo "Downloading headless Chromium..."
curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-55/stable-headless-chromium-amazonlinux-2017-03.zip > temp_downloads/headless-chromium.zip
unzip -q temp_downloads/headless-chromium.zip -d temp_downloads/
mv temp_downloads/headless-chromium selenium-layer/bin/
chmod 755 selenium-layer/bin/headless-chromium

# Download ChromeDriver
echo "Downloading ChromeDriver..."
curl -SL https://chromedriver.storage.googleapis.com/2.43/chromedriver_linux64.zip > temp_downloads/chromedriver.zip
unzip -q temp_downloads/chromedriver.zip -d temp_downloads/
mv temp_downloads/chromedriver selenium-layer/bin/
chmod 755 selenium-layer/bin/chromedriver

# Create the layer ZIP file
echo "Creating layer ZIP file..."
cd selenium-layer
zip -r ../selenium_layer.zip .
cd ..

# Clean up
rm -rf selenium-layer temp_downloads

echo "Selenium layer created: selenium_layer.zip"
