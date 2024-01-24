import logging
import unittest
from datetime import date, timedelta
from unittest.mock import Mock, mock_open, patch

import requests
from zen_quotes.zen_quotes import Quote, QuoteMode, Quotes, QuotesModel, logger

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
    def test_is_update_required(self) -> None:
        quotes = Quotes()
        self.assertIs(quotes.is_update_required(), True)

        quotes.quotes = QuotesModel(
            last_update=date.today(),
            today=[Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])],
            quotes=[
                Quote(quote=quote["q"], author=quote["a"]) for quote in QUOTES
            ],
        )
        self.assertIs(quotes.is_update_required(), False)

        quotes.quotes.last_update -= timedelta(days=1)
        self.assertIs(quotes.is_update_required(), True)


class TestQuotesRead(unittest.TestCase):
    def test_read(self) -> None:
        read_data = QuotesModel(
            last_update=date.today(),
            today=[Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])],
            quotes=[
                Quote(quote=quote["q"], author=quote["a"]) for quote in QUOTES
            ],
        ).model_dump_json(indent=4)

        quotes = Quotes()
        with patch(
            "zen_quotes.zen_quotes.open", new=mock_open(read_data=read_data)
        ):
            quotes.read()
        assert quotes.quotes is not None
        self.assertEqual(quotes.quotes.model_dump_json(indent=4), read_data)

    def test_read_file_not_found(self) -> None:
        quotes = Quotes()
        with patch(
            "zen_quotes.zen_quotes.open",
            new=Mock(side_effect=FileNotFoundError),
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            quotes.read()
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                "Output file not found: output/zen_quotes.json",
            )
        self.assertIsNone(quotes.quotes)

    def test_read_invalid_json(self) -> None:
        read_data = QuotesModel(
            last_update=date.today(),
            today=[Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])],
            quotes=[
                Quote(quote=quote["q"], author=quote["a"]) for quote in QUOTES
            ],
        ).model_dump_json(indent=4)
        read_data = read_data.replace("today", "oday", 1)

        quotes = Quotes()
        with patch(
            "zen_quotes.zen_quotes.open",
            new=mock_open(read_data=read_data),
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            quotes.read()
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                "Error parsing output file: output/zen_quotes.json",
            )
        self.assertIsNone(quotes.quotes)


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
