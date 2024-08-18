import time
import random
import logging
from dataclasses import dataclass

import pyautogui
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from undetected_playwright import stealth_sync
from sqlalchemy import text
from rich.logging import RichHandler
from rich import print
# from db.session import SessionLocal
# from db.models.proxy import Proxy
# from db.session import init_db
from config import config

@dataclass
class BrowserResult:
    type: str # "html" or "headers"
    content: str
    status: str
    url: str
    is_captcha: bool


class CaptchaSolver:
    def __init__(self):
        self.api_key = config.AZCAPTCHA_API_KEY

    def _get_captcha_solution(self, html):
        """ Get the captcha solution """
        logging.info("Starting captcha solution process.")
        
        # Extract captcha image URL or base64 data from the HTML
        soup = BeautifulSoup(html, "lxml")
        logging.debug("Parsed HTML with BeautifulSoup.")
        
        captcha_img = soup.select("div.captcha__img-container > img")
        
        if not captcha_img:
            logging.error("Captcha image not found in the HTML.")
            raise ValueError("Captcha image not found in the HTML")

        captcha_url = captcha_img[0]['src']
        logging.info("Captcha image found.")

        # Prepare the data to send to AZcaptcha
        if captcha_url.startswith('data:'):
            logging.info("Captcha image is embedded in base64 format.")
            # If the captcha is in base64 format (embedded image)
            captcha_data = captcha_url.split(',')[1]
            data = {
                'key': self.api_key,
                'method': 'base64',
                'body': captcha_data,
            }
            files = None  # No file needed in this case
        else:
            logging.info("Captcha image is an external URL, downloading...")
            # If the captcha is an external image, download it
            captcha_image_response = requests.get(captcha_url)
            if captcha_image_response.status_code != 200:
                logging.error(f"Failed to download captcha image, status code: {captcha_image_response.status_code}")
                raise Exception("Failed to download captcha image.")
            data = {
                'key': self.api_key,
                'method': 'post',
            }
            files = {
                'file': ('captcha.jpg', captcha_image_response.content),
            }

        # Send the captcha to AZcaptcha
        logging.info("Submitting captcha to AZcaptcha.")
        response = requests.post(
            url="https://azcaptcha.com/in.php",
            data=data,
            files=files
        )

        if response.text.split('|')[0] != 'OK':
            logging.error(f"Failed to submit captcha: {response.text}")
            raise Exception(f"Failed to submit captcha: {response.text}")
        
        captcha_id = response.text.split('|')[1]
        logging.info(f"Captcha submitted successfully, captcha ID: {captcha_id}")

        # Wait for the captcha solution
        for attempt in range(10):  # Retry up to 10 times
            logging.info(f"Attempt {attempt + 1}: Waiting for captcha solution...")
            time.sleep(5)  # Wait 5 seconds between retries
            result_response = requests.get(
                url="https://azcaptcha.com/res.php",
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                }
            )

            if result_response.text == 'CAPCHA_NOT_READY':
                logging.info("Captcha not ready yet.")
                continue
            elif result_response.text.split('|')[0] == 'OK':
                logging.info("Captcha solved successfully.")
                return result_response.text.split('|')[1]
            else:
                logging.error(f"Error retrieving captcha solution: {result_response.text}")
                raise Exception(f"Error retrieving captcha solution: {result_response.text}")

        logging.error("Captcha solution retrieval timed out.")
        raise Exception("Captcha solution retrieval timed out")

    def type_captcha_solution(self, solution: str, page, input_selector):
        """ Types the captcha solution into the input element using pyautogui with random intervals. """
        # Click the input field to focus it
        page.click(input_selector)
        
        for char in solution:
            pyautogui.typewrite(char)
            time.sleep(random.uniform(0.05, 0.3))  # Random delay between 50ms and 300ms

class BethovenScraper:
    def __init__(self, url):
        logging.debug("Initializing BethovenScraper")
        # init_db()
        
        self.main_url = url
        self.proxies = self.__get_all_proxies()
        self.playwright_proxies = self.__get_playwright_proxies(self.proxies)
    def __get_all_proxies(self):  
        """ Fetch all proxies from the database """
        test_proxies = [
            {"all://" : 'http://14a198a80f650:d19132986e@81.31.235.165:12323'},
            {"all://" : 'http://14a198a80f650:d19132986e@81.31.235.10:12323'},
            {"all://" : 'http://14a198a80f650:d19132986e@193.108.112.192:12323'},
            {"all://" : 'http://14a198a80f650:d19132986e@14.102.225.246:12323'},
            {"all://" : 'http://14a198a80f650:d19132986e@212.192.6.198:12323'}
        ]

        return test_proxies
        # session = SessionLocal

        # logging.debug("Fetching all proxies from the database")

        # try:
        #     proxies = session.query(Proxy).all()
        #     logging.info(f"Fetched {len(proxies)} proxies")
        #     proxy_strings = [proxy_obj.proxy for proxy_obj in proxies]
        #     return proxy_strings
        
        # except Exception as e:
        #     logging.error(f"Error fetching proxies: {e}")
        #     raise
        
        # finally:
        #     session.close()
        #     logging.debug("Session closed after fetching proxies")

    def __get_playwright_proxies(self, proxies):
        """ Convert the proxy strings to Playwright format """
        playwright_proxies = []
        for proxy in proxies:
            temp = proxy["all://"].replace("http://", "").split("@")
            z = [x for x in temp[0].split(":")] + [x for x in temp[1].split(":")]
            playwright_proxies.append({"username": z[0], "password": z[1], "host": z[2], "port": z[3]})

        return playwright_proxies

    def _check_if_captcha(self, html):
        """ Check if the page is a captcha page """
        logging.debug("Starting captcha check.")
        
        result = False
        logging.debug("Initializing BeautifulSoup with the provided HTML content.")
        soup = BeautifulSoup(html, "lxml")
        
        logging.debug("Searching for a div with class 'captcha'.")
        captcha_block = soup.find("div", class_="captcha")
        
        if captcha_block:
            logging.debug("Captcha block found in the HTML.")
            result = True
        else:
            logging.debug("No captcha block found in the HTML.")
        
        logging.debug(f"Captcha check result: {result}")
        return result
    
    def _get_captcha_solution(self, html):
        """ Get the captcha solution """
        pass

    def _check_main_url(self):
        if not self.main_url:
            logging.error("Main URL is not set")
            raise ValueError("Main URL is not set")
        logging.debug(f"Main URL is set: {self.main_url}")

    def scrape_html(self, url):
        with sync_playwright() as p:
            try: 
                browser = p.chromium.launch(headless=False)
                logging.debug("Launched Chromium browser")
                page = browser.new_page()
                context = browser.new_context(ignore_https_errors=True)
                stealth_sync(context)
                logging.debug("Created new browser context with stealth mode")
                page = context.new_page()
                page.goto(self.main_url)
                logging.info(f"Navigated to {self.main_url}")
                html = page.content()
                result = BrowserResult(type="html",
                                       content=html, 
                                       status="success", 
                                       url=url, 
                                       is_captcha=self._check_if_captcha(html))
                # Here it's important to check if It's captcha page
                if result.is_captcha:
                    solver = CaptchaSolver()
                    captcha_solution = solver._get_captcha_solution(result.content)
                    
                    # Assume the input field for captcha is found by some selector like "input[name='captcha']"
                    solver.type_captcha_solution(captcha_solution, page, "input[name='captcha']")
                    
                    # Submit the form after entering the captcha
                    page.click("button[class='captcha__btn-check']")

                time.sleep(5)        

                logging.info("Successfully scraped the main page content")
            
            except Exception as e:
                logging.error(f"Error during scraping: {e}")
            
            finally:
                if 'browser' in locals() and browser.is_connected():
                    browser.close()
                    logging.debug("Browser and context closed")
                
                return result
            
    def scrape_main_page(self):
        """ Scrape the main page of the website """
        logging.info(f"Starting to scrape the main page: {self.main_url}")
        self._check_main_url()
        result = None
        html = self.scrape_html(self.main_url)
        return html
            
        
# This is for testing in local environment
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    url = "https://www.bethowen.ru/"
    scraper = BethovenScraper(url)
    html = scraper.scrape_main_page()
    
    