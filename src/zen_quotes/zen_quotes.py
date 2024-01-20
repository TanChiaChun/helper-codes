"""Get quote from Zen Quotes."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests


class QuoteMode(Enum):
    """Quote mode to be sent to Zen Quotes."""

    TODAY = "today"
    QUOTES = "quotes"


@dataclass
class Quote:
    """Quote from Zen Quotes."""

    quote: str = ""
    author: str = ""


class Quotes:
    """List of Quotes from Zen Quotes."""

    def __init__(self) -> None:
        self.quotes_today: Optional[list[Quote]] = None
        self.quotes: Optional[list[Quote]] = None

    def request(self, quote_mode: QuoteMode) -> Optional[list[Quote]]:
        """Request quote from Zen Quotes.

        Args:
            quote_mode:
                Quote mode to Zen Quotes.

        Returns:
            List of Quote, else None when error.
        """
        try:
            r = requests.get(
                f"https://zenquotes.io/api/{quote_mode.value}", timeout=10
            )
        except (requests.ConnectionError, requests.Timeout):
            return None

        if r.status_code != 200:
            return None

        j = r.json()

        return [Quote(quote["q"], quote["a"]) for quote in j]

    def run(self) -> None:
        """Request & update quotes."""
        self.quotes_today = self.request(QuoteMode.TODAY)
        self.quotes = self.request(QuoteMode.QUOTES)


def main() -> None:
    """Main function."""
    print("hello")


if __name__ == "__main__":
    main()
