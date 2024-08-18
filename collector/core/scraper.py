import logging

from playwright.sync_api import sync_playwright
from undetected_playwright import stealth_sync
from sqlalchemy import text

from db.session import SessionLocal
from db.models.proxy import Proxy
from db.session import init_db

class BethovenScraper:
    def __init__(self, url):
        logging.debug("Initializing BethovenScraper")
        init_db()
        
        self.main_url = url
        self.proxies = self.__get_all_proxies()

    def __get_all_proxies(self):  
        session = SessionLocal

        logging.debug("Fetching all proxies from the database")

        try:
            proxies = session.query(Proxy).all()
            logging.info(f"Fetched {len(proxies)} proxies")
            proxy_strings = [proxy_obj.proxy for proxy_obj in proxies]
            return proxy_strings
        
        except Exception as e:
            logging.error(f"Error fetching proxies: {e}")
            raise
        
        finally:
            session.close()
            logging.debug("Session closed after fetching proxies")

    def check_main_url(self):
        if not self.main_url:
            logging.error("Main URL is not set")
            raise ValueError("Main URL is not set")
        logging.debug(f"Main URL is set: {self.main_url}")
    
    def scrape_html(self, url):
        with sync_playwright() as p:
            try: 
                browser = p.chromium.launch(headless=True)
                logging.debug("Launched Chromium browser")
                page = browser.new_page()
                context = browser.new_context(ignore_https_errors=True)
                stealth_sync(context)
                logging.debug("Created new browser context with stealth mode")
                page = context.new_page()
                page.goto(self.main_url)
                logging.info(f"Navigated to {self.main_url}")
                html = page.content()
                result = html
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
        self.check_main_url()
        result = None
        html = self.scrape_html(self.main_url)
        return html
            
        