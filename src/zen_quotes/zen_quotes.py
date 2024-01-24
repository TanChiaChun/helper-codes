"""Get quote from Zen Quotes."""

import logging
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional, TypeAlias

import requests
from pydantic import BaseModel, ValidationError

QuoteType: TypeAlias = dict[str, str]

logger = logging.getLogger(__name__)


class QuoteMode(Enum):
    """Quote mode to be sent to Zen Quotes."""

    TODAY = "today"
    QUOTES = "quotes"


class Quote(BaseModel):
    """Quote from Zen Quotes."""

    quote: str
    author: str


class QuotesModel(BaseModel):
    """List of Quotes from Zen Quotes."""

    last_update: date
    today: list[Quote]
    quotes: list[Quote]


class Quotes:
    """List of Quotes from Zen Quotes."""

    OUTPUT_DIR = Path("output")
    OUTPUT_FILE = Path(OUTPUT_DIR, "zen_quotes.json")

    def __init__(self) -> None:
        self.quotes: Optional[QuotesModel] = None

    def is_update_required(self) -> bool:
        """Return True if request of new quotes are required."""
        if self.quotes and self.quotes.last_update < date.today():
            return True
        if not self.quotes:
            return True
        return False

    def read(self) -> None:
        """Read quotes from JSON file.

        Skip if file not found or error parsing JSON.
        """
        try:
            with open(self.OUTPUT_FILE, encoding="utf8") as f:
                j = f.read()
        except FileNotFoundError:
            logger.warning("Output file not found: %s", self.OUTPUT_FILE)
            return

        try:
            self.quotes = QuotesModel.model_validate_json(j)
        except ValidationError:
            logger.warning("Error parsing output file: %s", self.OUTPUT_FILE)

    def request(self, quote_mode: QuoteMode) -> Optional[list[Quote]]:
        """Request quote from Zen Quotes.

        Args:
            quote_mode:
                Quote mode to Zen Quotes.

        Returns:
            List of Quote, else None when error.
        """
        get_url = f"https://zenquotes.io/api/{quote_mode.value}"
        try:
            r = requests.get(get_url, timeout=10)
        except requests.ConnectionError:
            logger.warning(
                "ConnectionError when requesting Zen Quotes: %s", get_url
            )
            return None
        except requests.Timeout:
            logger.warning("Timeout when requesting Zen Quotes: %s", get_url)
            return None

        if r.status_code != 200:
            logger.warning("Invalid HTTP status code: %s", get_url)
            return None

        j = r.json()

        return [Quote(quote=quote["q"], author=quote["a"]) for quote in j]

    def write(self) -> None:
        """Write quotes to JSON file.

        Skip if None.
        """
        if not self.quotes:
            return

        if not self.OUTPUT_DIR.is_dir():
            self.OUTPUT_DIR.mkdir()

        with open(self.OUTPUT_FILE, mode="w", encoding="utf8") as f:
            f.write(self.quotes.model_dump_json(indent=4))

    def run(self) -> None:
        """Read from local JSON file & update if required."""
        self.read()

        if self.is_update_required():
            today = self.request(QuoteMode.TODAY)
            quotes = self.request(QuoteMode.QUOTES)
            if today and quotes:
                self.quotes = QuotesModel(
                    last_update=date.today(), today=today, quotes=quotes
                )
                self.write()


def configure_logger() -> None:
    """Configure logger."""
    logger.setLevel(logging.WARNING)
    logger.addHandler(logging.StreamHandler())


def main() -> None:
    """Main function."""
    configure_logger()
    print("hello")


if __name__ == "__main__":
    main()
