from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import logging
import re
import os
import requests
import json
import argparse
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voting_log.log"),
        logging.StreamHandler()
    ]
)

# Try to import fake_useragent, install if not available
try:
    from fake_useragent import UserAgent
except ImportError:
    logging.info("Installing fake-useragent package...")
    import subprocess
    subprocess.check_call(["pip", "install", "fake-useragent"])
    from fake_useragent import UserAgent

def get_free_proxies():
    """Get a list of free proxies from public sources"""
    proxies = []
    try:
        # Try to get proxies from a public API
        response = requests.get('https://www.proxyscan.io/api/proxy?format=json&type=https,http&limit=20')
        if response.status_code == 200:
            data = response.json()
            for proxy in data:
                ip = proxy.get('Ip', '')
                port = proxy.get('Port', '')
                if ip and port:
                    proxies.append(f"{ip}:{port}")
        
        # If we didn't get any proxies, use a fallback list
        if not proxies:
            logging.warning("Could not fetch proxies from API, using fallback list")
            proxies = [
                "103.152.112.162:80",
                "103.83.232.122:80",
                "103.149.130.38:80",
                "103.118.40.119:80",
                "103.216.103.163:80"
            ]
    except Exception as e:
        logging.error(f"Error fetching proxies: {e}")
        # Fallback to a few public proxies
        proxies = [
            "103.152.112.162:80",
            "103.83.232.122:80",
            "103.149.130.38:80",
            "103.118.40.119:80",
            "103.216.103.163:80"
        ]
    
    logging.info(f"Retrieved {len(proxies)} proxies")
    return proxies

def scroll_to_element(driver, element):
    """Scroll to make the element visible in the viewport"""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
    time.sleep(random.uniform(0.5, 1.5))

def is_vote_successful(driver):
    """Check if the vote was successful by looking for success indicators"""
    try:
        # Look for common success indicators
        success_patterns = [
            "Thank you for voting",
            "Your vote has been recorded",
            "Results",
            "View Results"
        ]
        
        page_text = driver.page_source
        for pattern in success_patterns:
            if pattern in page_text:
                logging.info(f"Success indicator found: '{pattern}'")
                return True
        
        # Check if the voting form is no longer present (replaced by results)
        try:
            # Try to find the voting form
            voting_form = driver.find_element(By.XPATH, "//form[contains(@id, 'polls')]//ul[contains(@class, 'wp-polls-ul')]")
            # If we found it, check if it's still visible
            if not voting_form.is_displayed():
                logging.info("Voting form is no longer visible, vote likely successful")
                return True
        except NoSuchElementException:
            logging.info("Voting form no longer found, vote likely successful")
            return True
        
        # Check if results are displayed
        results_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'wp-polls-result') or contains(@class, 'pollresult') or contains(@class, 'results')]")
        if results_elements:
            logging.info("Results are now displayed, vote likely successful")
            return True
            
        # Check for percentage indicators which typically appear in results
        percentage_elements = driver.find_elements(By.XPATH, "//div[contains(text(), '%') or contains(@class, 'percent')]")
        if percentage_elements:
            logging.info("Percentage indicators found, vote likely successful")
            return True
            
        # Check if the page structure has changed significantly
        if "pollresult" in page_text or "poll-result" in page_text or "results" in page_text.lower():
            logging.info("Poll result text found in page, vote likely successful")
            return True
            
        return False
    except Exception as e:
        logging.error(f"Error checking vote success: {e}")
        return False

def vote_once(voting_url, target_candidate, max_retries=3, use_proxy=True, use_incognito=True):
    """
    Attempt to vote once with retry logic for handling errors
    
    Args:
        voting_url: URL of the voting page
        target_candidate: Name of the candidate to vote for
        max_retries: Maximum number of retry attempts for this voting session
        use_proxy: Whether to use proxy servers
        use_incognito: Whether to use incognito mode
    
    Returns:
        bool: True if vote was successful, False otherwise
    """
    retry_count = 0
    proxies = get_free_proxies() if use_proxy else []
    
    logging.info(f"Voting for candidate: {target_candidate}")
    logging.info(f"Voting URL: {voting_url}")
    
    while retry_count <= max_retries:
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        
        # Use incognito mode to avoid cookies
        if use_incognito:
            options.add_argument("--incognito")
        
        # Add random user agent
        try:
            ua = UserAgent()
            user_agent = ua.random
            logging.info(f"Using user agent: {user_agent}")
        except:
            # Fallback user agents if fake_useragent fails
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
            ]
            user_agent = random.choice(user_agents)
            logging.info(f"Using fallback user agent: {user_agent}")
        
        options.add_argument(f"user-agent={user_agent}")
        
        # Use proxy if available
        if use_proxy and proxies:
            proxy = random.choice(proxies)
            logging.info(f"Using proxy: {proxy}")
            options.add_argument(f'--proxy-server={proxy}')
        
        # Disable automation flags to avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Additional options to avoid detection
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the Chrome driver
        driver = None
        
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            # Mask WebDriver to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Clear cookies and cache
            driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
            driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            
            # Open the website
            logging.info(f"Opening website (attempt {retry_count + 1}/{max_retries + 1})")
            driver.get(voting_url)
            
            # Wait for the page to fully load with increased timeout
            wait = WebDriverWait(driver, 45)  # Increased timeout
            
            # Check if we got a 503 error
            if "503" in driver.title or "Service Unavailable" in driver.page_source:
                logging.warning("503 Service Unavailable detected. Retrying...")
                retry_count += 1
                if driver:
                    driver.quit()
                # Wait longer between retries
                time.sleep(random.uniform(30, 45))
                continue
            
            # Wait for the page to be fully loaded
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                logging.info("Page fully loaded")
            except TimeoutException:
                logging.warning("Timeout waiting for page to load completely")
            
            # Add random delay to simulate human behavior
            time.sleep(random.uniform(3, 7))
            
            # Check if we're already seeing results (which means we've already voted)
            if is_vote_successful(driver):
                logging.info("Vote results already showing - we may have already voted or vote was recorded automatically")
                
                # If we're using a proxy, try a different one
                if use_proxy and len(proxies) > 1:
                    current_proxy = proxy if 'proxy' in locals() else None
                    if current_proxy in proxies:
                        proxies.remove(current_proxy)
                    logging.info(f"Removing used proxy. {len(proxies)} proxies remaining.")
                    retry_count += 1
                    if driver:
                        driver.quit()
                    continue
                else:
                    return True
            
            # Find all voting options
            try:
                logging.info("Looking for voting options")
                
                # Find all radio buttons and their labels
                radio_buttons = driver.find_elements(By.XPATH, "//input[@type='radio']")
                
                if not radio_buttons:
                    logging.warning("No radio buttons found on the page")
                    
                    # Check if we're seeing results already
                    if is_vote_successful(driver):
                        logging.info("No voting options found, but results are displayed - vote likely already counted")
                        return True
                    else:
                        raise Exception("Could not find any voting options")
                
                # Find the option for our target candidate
                target_option = None
                
                for radio in radio_buttons:
                    try:
                        # Get the ID of the radio button
                        radio_id = radio.get_attribute("id")
                        if not radio_id:
                            continue
                            
                        # Find the associated label
                        label = driver.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                        label_text = label.text
                        
                        logging.info(f"Found option: {label_text}")
                        
                        # Check if this is our target candidate
                        if target_candidate in label_text:
                            target_option = radio
                            logging.info(f"Found target candidate: {label_text}")
                            break
                    except Exception as e:
                        logging.warning(f"Error processing radio button: {e}")
                        continue
                
                # If target candidate not found, choose a random option
                if not target_option and radio_buttons:
                    target_option = random.choice(radio_buttons)
                    logging.info(f"Target candidate not found, using random option")
                
                if not target_option:
                    raise Exception("Could not find any usable voting options")
                
                # Scroll to the element to make sure it's in view
                scroll_to_element(driver, target_option)
                
                # Click with ActionChains for more reliable clicking
                actions = ActionChains(driver)
                actions.move_to_element(target_option).click().perform()
                logging.info("Clicked on voting option")
                
                # Wait a bit to ensure the click is registered with random delay
                time.sleep(random.uniform(2, 4))
                
                # Try to find and click the vote button
                vote_buttons = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit']")
                
                vote_button = None
                for button in vote_buttons:
                    try:
                        value = button.get_attribute("value")
                        if value and ("vote" in value.lower() or "submit" in value.lower()):
                            vote_button = button
                            logging.info(f"Found vote button with value: {value}")
                            break
                    except:
                        continue
                
                if not vote_button:
                    # If we can't find the vote button, check if we're seeing results already
                    if is_vote_successful(driver):
                        logging.info("No vote button found, but results are displayed - vote likely already counted")
                        return True
                    else:
                        raise Exception("Could not find vote button")
                
                # Scroll to make vote button visible
                scroll_to_element(driver, vote_button)
                
                # Try different click methods
                click_success = False
                try:
                    logging.info("Attempting to click vote button with ActionChains")
                    actions = ActionChains(driver)
                    actions.move_to_element(vote_button).click().perform()
                    click_success = True
                except ElementClickInterceptedException:
                    try:
                        logging.info("ActionChains failed, trying JavaScript click")
                        driver.execute_script("arguments[0].click();", vote_button)
                        click_success = True
                    except:
                        try:
                            logging.info("JavaScript click failed, trying direct click")
                            vote_button.click()
                            click_success = True
                        except:
                            logging.error("All click methods failed")
                
                if not click_success:
                    raise Exception("Failed to click the vote button using all methods")
                
                logging.info("Vote button clicked, waiting for page to update")
                
                # Wait for page changes that indicate vote was processed
                time.sleep(random.uniform(5, 8))
                
                # Check if vote was successful
                if is_vote_successful(driver):
                    logging.info("Vote successfully submitted!")
                    
                    # Take a screenshot of the successful vote
                    try:
                        screenshot_file = f"successful_vote_{retry_count}.png"
                        driver.save_screenshot(screenshot_file)
                        logging.info(f"Success screenshot saved as {screenshot_file}")
                    except Exception as e:
                        logging.error(f"Failed to save success screenshot: {e}")
                        
                    return True
                else:
                    logging.warning("Could not confirm if vote was successful")
                    
                    # Take a screenshot for debugging
                    try:
                        screenshot_file = f"vote_attempt_{retry_count}.png"
                        driver.save_screenshot(screenshot_file)
                        logging.info(f"Screenshot saved as {screenshot_file}")
                    except Exception as e:
                        logging.error(f"Failed to save screenshot: {e}")
                    
                    # If we're not sure, let's consider it a failure and retry
                    raise Exception("Could not confirm vote success")
                
            except Exception as e:
                logging.error(f"Error during voting process: {e}")
                retry_count += 1
                
                # Take a screenshot for debugging
                try:
                    if driver:
                        screenshot_file = f"error_screenshot_{retry_count}.png"
                        driver.save_screenshot(screenshot_file)
                        logging.info(f"Error screenshot saved as {screenshot_file}")
                except:
                    pass
                
                if retry_count <= max_retries:
                    # Exponential backoff with jitter
                    wait_time = (2 ** retry_count) + random.uniform(10, 20)
                    logging.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                continue
            
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            retry_count += 1
            if retry_count <= max_retries:
                # Exponential backoff with jitter
                wait_time = (2 ** retry_count) + random.uniform(10, 20)
                logging.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        finally:
            # Close the browser
            if driver:
                driver.quit()
    
    logging.warning("Max retries reached. Moving to next voting attempt.")
    return False

def main():
    """Main function to run the voting process multiple times"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Automated voting script')
    parser.add_argument('--url', type=str, default='https://example.com/voting-page/',
                        help='URL of the voting page')
    parser.add_argument('--candidate', type=str, default='CANDIDATE NAME',
                        help='Name of the candidate to vote for')
    parser.add_argument('--attempts', type=int, default=5,
                        help='Number of voting attempts')
    parser.add_argument('--retries', type=int, default=2,
                        help='Maximum retries per attempt')
    parser.add_argument('--proxy', action='store_true', default=True,
                        help='Use proxy servers')
    parser.add_argument('--no-proxy', dest='proxy', action='store_false',
                        help='Do not use proxy servers')
    parser.add_argument('--incognito', action='store_true', default=True,
                        help='Use incognito mode')
    parser.add_argument('--no-incognito', dest='incognito', action='store_false',
                        help='Do not use incognito mode')
    
    args = parser.parse_args()
    
    successful_votes = 0
    total_attempts = args.attempts
    
    logging.info(f"Starting voting automation - {total_attempts} attempts planned")
    logging.info(f"Target URL: {args.url}")
    logging.info(f"Target candidate: {args.candidate}")
    
    # Install required packages if not already installed
    try:
        import requests
    except ImportError:
        logging.info("Installing requests package...")
        import subprocess
        subprocess.check_call(["pip", "install", "requests"])
        import requests
    
    for i in range(total_attempts):
        logging.info(f"Running vote attempt {i+1} of {total_attempts}")
        
        if vote_once(args.url, args.candidate, max_retries=args.retries, use_proxy=args.proxy, use_incognito=args.incognito):
            successful_votes += 1
        
        # Wait between attempts with random delay to avoid detection
        if i < total_attempts - 1:  # Don't wait after the last attempt
            wait_time = random.uniform(30, 60)
            logging.info(f"Waiting {wait_time:.1f} seconds before next attempt...")
            time.sleep(wait_time)
    
    logging.info(f"All voting attempts completed! Successful votes: {successful_votes}/{total_attempts}")

if __name__ == "__main__":
    main()
