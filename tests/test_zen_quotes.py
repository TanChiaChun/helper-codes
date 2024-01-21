import logging
import unittest
from unittest.mock import Mock, patch

import requests
from zen_quotes.zen_quotes import Quote, QuoteMode, Quotes, logger

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
                [Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])],
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
                [
                    Quote(quote=quote["q"], author=quote["a"])
                    for quote in QUOTES
                ],
            )

    def test_request_quote_connection_error(self) -> None:
        with patch(
            "requests.get", new=Mock(side_effect=requests.ConnectionError)
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            self.assertIsNone(Quotes().request(QuoteMode.QUOTES))
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                (
                    "ConnectionError when requesting Zen Quotes: "
                    "https://zenquotes.io/api/quotes"
                ),
            )

    def test_request_quote_timeout(self) -> None:
        with patch(
            "requests.get", new=Mock(side_effect=requests.Timeout)
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            self.assertIsNone(Quotes().request(QuoteMode.QUOTES))
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                (
                    "Timeout when requesting Zen Quotes: "
                    "https://zenquotes.io/api/quotes"
                ),
            )

    def test_request_quote_error_status_code(self) -> None:
        with patch(
            "requests.get", new=Mock(return_value=Mock(status_code=201))
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            self.assertIsNone(Quotes().request(QuoteMode.QUOTES))
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                "Invalid HTTP status code: https://zenquotes.io/api/quotes",
            )


if __name__ == "__main__":
    unittest.main()
