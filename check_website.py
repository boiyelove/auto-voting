#!/usr/bin/env python3
import requests
import time
import argparse
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

def main():
    parser = argparse.ArgumentParser(description='Check if a website is accessible')
    parser.add_argument('--url', type=str, default='https://democracyheroesaward.com/iconic-senator-of-the-year/',
                        help='URL to check')
    parser.add_argument('--timeout', type=int, default=5,
                        help='Timeout in seconds')
    parser.add_argument('--interval', type=int, default=60,
                        help='Interval between checks in seconds')
    parser.add_argument('--count', type=int, default=5,
                        help='Number of checks to perform')
    args = parser.parse_args()
    
    print(f"Checking {args.url} with timeout {args.timeout}s, interval {args.interval}s, count {args.count}")
    print()
    
    for i in range(args.count):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status, elapsed = check_website(args.url, args.timeout)
        print(f"{timestamp} - Status: {status}, Elapsed: {elapsed:.2f}s")
        
        if i < args.count - 1:
            time.sleep(args.interval)

if __name__ == '__main__':
    main()
