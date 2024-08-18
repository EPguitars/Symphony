import os
import time
import logging

from rich.logging import RichHandler

from config import config
from scraper import BethovenScraper

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )


class BethovenCollector:
    def __init__(self):
        self.config = config
        self.logger = logging.getLogger("beethoven")

    def collect(self):
        print("Collecting data")
        main_url = self.config.SOURCE_URL
        scraper = BethovenScraper(main_url)
        main_page = scraper.scrape_main_page()


if __name__ == "__main__":
    setup_logging()
    collector = BethovenCollector()
    collector.collect()