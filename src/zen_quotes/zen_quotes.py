"""Get quote from Zen Quotes."""

from dataclasses import dataclass
from enum import Enum

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


def request_quote(quote_mode: QuoteMode) -> Quote | list[Quote] | None:
    """Request quote from Zen Quotes.

    Args:
        quote_mode:
            Quote mode to Zen Quotes.
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

    if len(j) == 1:
        return Quote(j[0]["q"], j[0]["a"])
    return [Quote(quote["q"], quote["a"]) for quote in j]


def main() -> None:
    """Main function."""
    print("hello")


if __name__ == "__main__":
    main()
