import time
import random
import logging
from dataclasses import dataclass
from itertools import cycle
import pyautogui
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from undetected_playwright import stealth_sync
from sqlalchemy import text
from rich.logging import RichHandler
from rich import print
from db.session import SessionLocal
from db.models.proxy import Proxy
from db.session import init_db
from config import config

@dataclass
class BrowserResult:
    """Represents the result of a browser scraping operation."""
    
    type: str  # "html" or "headers"
    content: str
    status: str
    url: str
    is_captcha: bool


@dataclass
class Proxy:
    """Holds proxy information for different contexts."""
    
    proxy_standart: dict
    proxy_playwright: dict
    headers: dict


class CaptchaSolver:
    """Handles the process of solving captchas using the AZcaptcha service."""

    def __init__(self):
        """Initialize the CaptchaSolver with the AZcaptcha API key."""
        self.api_key = config.AZCAPTCHA_API_KEY

    def _get_captcha_solution(self, html):
        """
        Get the captcha solution from AZcaptcha.

        Extracts the captcha image from the HTML and sends it to AZcaptcha for solving.

        Parameters:
        html (str): The HTML content of the page containing the captcha.

        Returns:
        str: The solution to the captcha.

        Raises:
        ValueError: If the captcha image is not found in the HTML.
        Exception: If there is an error during the captcha submission or retrieval.
        """
        logging.info("Starting captcha solution process.")
        
        soup = BeautifulSoup(html, "lxml")
        logging.debug("Parsed HTML with BeautifulSoup.")
        
        captcha_img = soup.select("div.captcha__img-container > img")
        
        if not captcha_img:
            logging.error("Captcha image not found in the HTML.")
            raise ValueError("Captcha image not found in the HTML")

        captcha_url = captcha_img[0]['src']
        logging.info("Captcha image found.")

        if captcha_url.startswith('data:'):
            logging.info("Captcha image is embedded in base64 format.")
            captcha_data = captcha_url.split(',')[1]
            data = {
                'key': self.api_key,
                'method': 'base64',
                'body': captcha_data,
            }
            files = None
        else:
            logging.info("Captcha image is an external URL, downloading...")
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

        for attempt in range(10):
            logging.info(f"Attempt {attempt + 1}: Waiting for captcha solution...")
            time.sleep(5)
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
        """
        Type the captcha solution into the input element using pyautogui with random intervals.

        Parameters:
        solution (str): The solved captcha to be typed.
        page: The Playwright page object where the captcha input is located.
        input_selector (str): The CSS selector for the captcha input field.
        """
        page.click(input_selector)
        
        for char in solution:
            pyautogui.typewrite(char)
            time.sleep(random.uniform(0.05, 0.3))


class BethovenScraper:
    """Scrapes the main page of the Bethoven website using proxies and handles captcha challenges."""

    def __init__(self, url):
        """
        Initialize the BethovenScraper with the main URL.

        Parameters:
        url (str): The main URL of the website to scrape.
        """
        logging.debug("Initializing BethovenScraper")
        # init_db()
        
        self.main_url = url
        self.proxies = self.__get_all_proxies()  # Generator
        
    def __get_all_proxies(self):  
        """
        Fetch all proxies from the database.

        Returns:
        generator: A cycle generator of Proxy objects.
        """
        result = []
        session = SessionLocal()

        logging.debug("Fetching all proxies from the database")

        try:
            proxies = session.query(Proxy).all()
            logging.info(f"Fetched {len(proxies)} proxies")
            proxies_standart = {"all://": proxy for proxy in proxies}
            for proxy in proxies_standart:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
                }
                playwright_proxy = self.__get_playwright_proxy(proxy)
                result.append(Proxy(proxy, 
                                    playwright_proxy, 
                                    headers))
            
            random.shuffle(result)
            
            return cycle(result)
        
        except Exception as e:
            logging.error(f"Error fetching proxies: {e}")
            raise
        
        finally:
            session.close()
            logging.debug("Session closed after fetching proxies")

    def __get_playwright_proxy(self, proxy):
        """
        Convert the proxy strings to Playwright format.

        Parameters:
        proxy (dict): A dictionary containing the proxy information.

        Returns:
        dict: A dictionary formatted for Playwright's proxy configuration.
        """
        proxy_string = proxy["all://"]
        temp = proxy_string.replace("http://", "").split("@")
        credentials, host_info = temp
        username, password = credentials.split(":")
        host, port = host_info.split(":")

        playwright_proxy = {
            "server": f"http://{host}:{port}",
            "username": username,
            "password": password
        }

        return playwright_proxy

    def _check_if_captcha(self, html):
        """
        Check if the page is a captcha page.

        Parameters:
        html (str): The HTML content of the page to check.

        Returns:
        bool: True if a captcha is detected, False otherwise.
        """
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
        """Get the captcha solution."""
        pass

    def _check_main_url(self):
        """
        Check if the main URL is set.

        Raises:
        ValueError: If the main URL is not set.
        """
        if not self.main_url:
            logging.error("Main URL is not set")
            raise ValueError("Main URL is not set")
        logging.debug(f"Main URL is set: {self.main_url}")

    def scrape_html(self, url, proxy):
        """
        Scrape the HTML content of the given URL using the provided proxy.

        Parameters:
        url (str): The URL of the page to scrape.
        proxy (Proxy): The proxy to use for scraping.

        Returns:
        BrowserResult: The result of the scraping operation, including the HTML content, status, and whether a captcha was detected.
        """
        with sync_playwright() as p:
            try: 
                browser = p.chromium.launch(headless=False, proxy=proxy.proxy_playwright)
                logging.debug("Launched Chromium browser")
                page = browser.new_page()
                context = browser.new_context(ignore_https_errors=True)
                stealth_sync(context)
                logging.debug("Created new browser context with stealth mode")
                page = context.new_page()
                page.goto(self.main_url, timeout=60000, wait_until="domcontentloaded")
                logging.info(f"Navigated to {self.main_url}")
                html = page.content()
                result = BrowserResult(type="html",
                                       content=html, 
                                       status="success", 
                                       url=url, 
                                       is_captcha=self._check_if_captcha(html))
                if result.is_captcha:
                    solver = CaptchaSolver()
                    captcha_solution = solver._get_captcha_solution(result.content)
                    
                    solver.type_captcha_solution(captcha_solution, page, "input[name='captcha']")
                    page.click("button[class='captcha__btn-check']")

                page.wait_for_load_state("domcontentloaded")     
                time.sleep(20)
                logging.info("Successfully scraped the main page content")
            
            except Exception as e:
                logging.error(f"Error during scraping: {e}")
            
            finally:
                if 'browser' in locals() and browser.is_connected():
                    browser.close()
                    logging.debug("Browser and context closed")
                
                return result
            
    def scrape_main_page(self, proxy):
        """
        Scrape the main page of the website.

        Parameters:
        proxy (Proxy): The proxy to use for scraping the main page.

        Returns:
        str: The HTML content of the main page.
        """
        logging.info(f"Starting to scrape the main page: {self.main_url}")
        self._check_main_url()
        result = None
        html = self.scrape_html(self.main_url, proxy)
        with open("main_page.html", "w", encoding="UTF=8") as file:
            file.write(html)
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
    proxy = next(scraper.proxies)
    html = scraper.scrape_main_page(proxy)
