import logging

from rich.logging import RichHandler

from config import config
from scraper import BethovenScraper

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )


class BethovenCollector:
    def __init__(self):
        self.config = config
        self.logger = logging.getLogger("beethoven")

    def collect(self):
        main_url = self.config["source_url"]
        scraper = BethovenScraper(main_url)