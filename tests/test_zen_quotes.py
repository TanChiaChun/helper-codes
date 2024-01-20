import unittest
from unittest.mock import Mock, patch

import requests
from zen_quotes.zen_quotes import Quote, QuoteMode, Quotes


class TestQuotesRequest(unittest.TestCase):
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
        with patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=[self.quotes[0]])
                )
            ),
        ):
            self.assertEqual(
                Quotes().request(QuoteMode.TODAY),
                [Quote(self.quotes[0]["q"], self.quotes[0]["a"])],
            )

    def test_request_quote_multiple(self) -> None:
        with patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=self.quotes)
                )
            ),
        ):
            self.assertEqual(
                Quotes().request(QuoteMode.QUOTES),
                [Quote(quote["q"], quote["a"]) for quote in self.quotes],
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
