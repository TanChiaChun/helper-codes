import unittest
from unittest.mock import Mock, patch

import requests
from zen_quotes.zen_quotes import Quote, QuoteMode, Quotes

QUOTES = [
    {
        "q": "A crisis is an opportunity riding the dangerous wind.",
        "a": "Chinese Proverb",
    },
    {
        "q": "Till it has loved, no man or woman can become itself.",
        "a": "Emily Dickinson",
    },
]


class TestQuotes(unittest.TestCase):
    def test_to_json(self) -> None:
        quotes = Quotes()
        quotes.quotes_today = [Quote(QUOTES[0]["q"], QUOTES[0]["a"])]
        quotes.quotes = [Quote(quote["q"], quote["a"]) for quote in QUOTES]

        expected = {
            "today": {"quote": QUOTES[0]["q"], "author": QUOTES[0]["a"]},
            "quotes": [
                {"quote": QUOTES[0]["q"], "author": QUOTES[0]["a"]},
                {"quote": QUOTES[1]["q"], "author": QUOTES[1]["a"]},
            ],
        }
        self.assertDictEqual(quotes.to_json(), expected)


class TestQuotesRequest(unittest.TestCase):
    def test_request_quote_single(self) -> None:
        with patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=[QUOTES[0]])
                )
            ),
        ):
            self.assertEqual(
                Quotes().request(QuoteMode.TODAY),
                [Quote(QUOTES[0]["q"], QUOTES[0]["a"])],
            )

    def test_request_quote_multiple(self) -> None:
        with patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=QUOTES)
                )
            ),
        ):
            self.assertEqual(
                Quotes().request(QuoteMode.QUOTES),
                [Quote(quote["q"], quote["a"]) for quote in QUOTES],
            )

    def test_request_quote_connection_error(self) -> None:
        with patch(
            "requests.get", new=Mock(side_effect=requests.ConnectionError)
        ):
            self.assertEqual(Quotes().request(QuoteMode.QUOTES), None)

    def test_request_quote_timeout(self) -> None:
        with patch("requests.get", new=Mock(side_effect=requests.Timeout)):
            self.assertEqual(Quotes().request(QuoteMode.QUOTES), None)

    def test_request_quote_error_status_code(self) -> None:
        with patch(
            "requests.get", new=Mock(return_value=Mock(status_code=201))
        ):
            self.assertEqual(Quotes().request(QuoteMode.QUOTES), None)


if __name__ == "__main__":
    unittest.main()
