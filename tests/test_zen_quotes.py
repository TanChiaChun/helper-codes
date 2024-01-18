import unittest
from unittest.mock import Mock, patch

import requests
from zen_quotes.zen_quotes import Quote, QuoteMode, request_quote


class TestRequestQuote(unittest.TestCase):
    def setUp(self) -> None:
        self.quotes = [
            {
                "q": "A crisis is an opportunity riding the dangerous wind.",
                "a": "Chinese Proverb",
            },
            {
                "q": "Till it has loved, no man or woman can become itself.",
                "a": "Emily Dickinson",
            },
        ]

    def test_request_quote_single(self) -> None:
        patcher = patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=[self.quotes[0]])
                )
            ),
        )
        patcher.start()
        self.assertEqual(
            request_quote(QuoteMode.TODAY),
            [Quote(self.quotes[0]["q"], self.quotes[0]["a"])],
        )
        patcher.stop()

    def test_request_quote_multiple(self) -> None:
        patcher = patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=self.quotes)
                )
            ),
        )
        patcher.start()
        self.assertEqual(
            request_quote(QuoteMode.QUOTES),
            [Quote(quote["q"], quote["a"]) for quote in self.quotes],
        )
        patcher.stop()

    def test_request_quote_connection_error(self) -> None:
        patcher = patch(
            "requests.get", new=Mock(side_effect=requests.ConnectionError)
        )
        patcher.start()
        self.assertEqual(request_quote(QuoteMode.QUOTES), None)
        patcher.stop()

    def test_request_quote_timeout(self) -> None:
        patcher = patch("requests.get", new=Mock(side_effect=requests.Timeout))
        patcher.start()
        self.assertEqual(request_quote(QuoteMode.QUOTES), None)
        patcher.stop()

    def test_request_quote_error_status_code(self) -> None:
        patcher = patch(
            "requests.get", new=Mock(return_value=Mock(status_code=201))
        )
        patcher.start()
        self.assertEqual(request_quote(QuoteMode.QUOTES), None)
        patcher.stop()


if __name__ == "__main__":
    unittest.main()
