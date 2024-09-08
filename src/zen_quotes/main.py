"""Get quote from Zen Quotes."""

import logging
from datetime import date
from enum import Enum
from pathlib import Path
from random import choice
from typing import Optional

import requests
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class QuoteMode(Enum):
    """Quote mode to be sent to Zen Quotes."""

    TODAY = "today"
    QUOTES = "quotes"


class Quote(BaseModel):
    """Quote from Zen Quotes."""

    quote: str
    author: str

    def __str__(self) -> str:
        return f"{self.quote} - {self.author}"


class QuotesModel(BaseModel):
    """List of Quotes from Zen Quotes."""

    last_update: date
    today: list[Quote]
    quotes: list[Quote]


class QuotesStorage:
    """File I/O for `QuotesModel`."""

    _OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
    _OUTPUT_FILE = _OUTPUT_DIR / "zen_quotes.json"

    @classmethod
    def read(cls) -> QuotesModel:
        """Read quotes from JSON file.

        Returns:
           `QuotesModel` instance.

        Raises:
            FileNotFoundError:
                Output file not found.
            pydantic.ValidationError:
                Error parsing output file.
        """
        try:
            j = cls._OUTPUT_FILE.read_text(encoding="utf8")
        except FileNotFoundError:
            logger.warning(
                "Output file not found: %s", cls._OUTPUT_FILE.as_posix()
            )
            raise

        try:
            quotes = QuotesModel.model_validate_json(j)
        except ValidationError:
            logger.warning(
                "Error parsing output file: %s", cls._OUTPUT_FILE.as_posix()
            )
            raise

        return quotes

    @classmethod
    def write(cls, quotes: QuotesModel) -> None:
        """Write quotes to JSON file.

        - Create output directory if not exist.

        Args:
            quotes:
                `QuotesModel` instance to be written.
        """
        if not cls._OUTPUT_DIR.is_dir():
            cls._OUTPUT_DIR.mkdir()

        cls._OUTPUT_FILE.write_text(
            quotes.model_dump_json(indent=4), encoding="utf8"
        )


class Quotes:
    """List of Quotes from Zen Quotes."""

    def __init__(self) -> None:
        self.quotes: Optional[QuotesModel]
        try:
            self.quotes = QuotesStorage.read()
        except (FileNotFoundError, ValidationError):
            self.quotes = None

    def print(self) -> None:
        """Print TODAY quote and 1 quote randomly from QUOTES."""
        if self.quotes:
            print("TODAY:")
            print(self.quotes.today[0])
            print("")
            print("RANDOM:")
            print(choice(self.quotes.quotes))

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

    def run(self) -> None:
        """Read from local JSON file & update if required."""
        if self._is_update_required():
            print("Requesting new quotes")

            today = self.request(QuoteMode.TODAY)
            quotes = self.request(QuoteMode.QUOTES)
            if today and quotes:
                self.quotes = QuotesModel(
                    last_update=date.today(), today=today, quotes=quotes
                )
                QuotesStorage.write(self.quotes)

        self.print()

    def _is_update_required(self) -> bool:
        """Return True if request of new quotes is required."""
        if self.quotes and self.quotes.last_update == date.today():
            return False
        return True


def main() -> None:
    """Main function."""
    logging.basicConfig()

    Quotes().run()


if __name__ == "__main__":
    main()
