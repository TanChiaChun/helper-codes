"""Get quote from Zen Quotes."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, TypeAlias

import requests

QuoteType: TypeAlias = dict[str, str]


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

    def to_json(self) -> dict[str, QuoteType | list[QuoteType]]:
        """Return class JSON representation."""
        j: dict[str, QuoteType | list[QuoteType]] = {}

        if self.quotes_today:
            j[QuoteMode.TODAY.value] = self.quotes_today[0].__dict__
        if self.quotes:
            j[QuoteMode.QUOTES.value] = [
                quote.__dict__ for quote in self.quotes
            ]

        return j

    def write(self) -> None:
        """Write quotes to JSON file."""
        output_dir = Path("output")
        if not output_dir.is_dir():
            output_dir.mkdir()

        with open(
            Path(output_dir, "zen_quotes.json"), mode="w", encoding="utf8"
        ) as f:
            json.dump(self.to_json(), f, indent=4)

    def run(self) -> None:
        """Request quotes & write to JSON on success."""
        self.quotes_today = self.request(QuoteMode.TODAY)
        self.quotes = self.request(QuoteMode.QUOTES)

        if self.quotes_today and self.quotes:
            self.write()


def main() -> None:
    """Main function."""
    print("hello")


if __name__ == "__main__":
    main()
