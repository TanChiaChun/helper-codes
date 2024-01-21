"""Get quote from Zen Quotes."""

import logging
from enum import Enum
from pathlib import Path
from typing import Optional, TypeAlias

import requests
from pydantic import BaseModel

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

    today: list[Quote]
    quotes: list[Quote]


class Quotes:
    """List of Quotes from Zen Quotes."""

    def __init__(self) -> None:
        self.quotes: Optional[QuotesModel] = None

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

        output_dir = Path("output")
        if not output_dir.is_dir():
            output_dir.mkdir()

        with open(
            Path(output_dir, "zen_quotes.json"), mode="w", encoding="utf8"
        ) as f:
            f.write(self.quotes.model_dump_json(indent=4))

    def run(self) -> None:
        """Request quotes & write to JSON on success."""
        today = self.request(QuoteMode.TODAY)
        quotes = self.request(QuoteMode.QUOTES)
        if today and quotes:
            self.quotes = QuotesModel(today=today, quotes=quotes)
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
