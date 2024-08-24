import logging
import unittest
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import requests

from zen_quotes.main import Quote, QuoteMode, Quotes, QuotesModel, logger

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
QUOTES_MODEL = QuotesModel(
    last_update=date.today(),
    today=[Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])],
    quotes=[Quote(quote=quote["q"], author=quote["a"]) for quote in QUOTES],
)


class TestQuote(unittest.TestCase):
    def test_str(self) -> None:
        self.assertEqual(
            str(Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])),
            f"{QUOTES[0]['q']} - {QUOTES[0]['a']}",
        )


class TestQuotes(unittest.TestCase):
    def test_is_update_required_false(self) -> None:
        quotes = Quotes()
        quotes.quotes = QUOTES_MODEL
        self.assertIs(quotes.is_update_required(), False)

    def test_is_update_required_true_empty_quotes(self) -> None:
        quotes = Quotes()
        self.assertIs(quotes.is_update_required(), True)

    def test_is_update_required_true_outdated(self) -> None:
        quotes = Quotes()
        quotes.quotes = QUOTES_MODEL
        quotes.quotes.last_update -= timedelta(days=1)
        self.assertIs(quotes.is_update_required(), True)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print(self, mock_stdout: StringIO) -> None:
        quotes = Quotes()
        quotes.quotes = QUOTES_MODEL

        expected = (
            "TODAY:\n"
            f"{QUOTES[0]['q']} - {QUOTES[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{QUOTES[1]['q']} - {QUOTES[1]['a']}"
            "\n"
        )
        with patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=quotes.quotes.quotes[1]),
        ):
            quotes.print()
        self.assertEqual(mock_stdout.getvalue(), expected)

    @patch("sys.stdout", new_callable=StringIO)
    def test_run_print_only(self, mock_stdout: StringIO) -> None:
        with patch(
            "zen_quotes.main.open",
            new=Mock(side_effect=FileNotFoundError),
        ), patch(
            "requests.get", new=Mock(side_effect=requests.ConnectionError)
        ):
            Quotes().run()
        self.assertEqual(mock_stdout.getvalue(), "Requesting new quotes\n")


class TestQuotesRead(unittest.TestCase):
    def test_read(self) -> None:
        read_data = QUOTES_MODEL.model_dump_json(indent=4)

        quotes = Quotes()
        with patch("zen_quotes.main.open", new=mock_open(read_data=read_data)):
            quotes.read()
        assert quotes.quotes is not None
        self.assertEqual(quotes.quotes.model_dump_json(indent=4), read_data)

    def test_read_file_not_found(self) -> None:
        quotes = Quotes()
        with patch(
            "zen_quotes.main.open",
            new=Mock(side_effect=FileNotFoundError),
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            quotes.read()

            output_file = (
                Path(__file__).parent.parent.parent
                / "output"
                / "zen_quotes.json"
            )
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                f"Output file not found: {output_file.as_posix()}",
            )
        self.assertIsNone(quotes.quotes)

    def test_read_invalid_json(self) -> None:
        read_data = QUOTES_MODEL.model_dump_json(indent=4)
        read_data = read_data.replace("today", "oday", 1)

        quotes = Quotes()
        with patch(
            "zen_quotes.main.open",
            new=mock_open(read_data=read_data),
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            quotes.read()

            output_file = (
                Path(__file__).parent.parent.parent
                / "output"
                / "zen_quotes.json"
            )
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                f"Error parsing output file: {output_file.as_posix()}",
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


class TestModule(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_main(self, mock_stdout: StringIO) -> None:
        read_data = QUOTES_MODEL.model_dump_json(indent=4)
        expected = (
            "TODAY:\n"
            f"{QUOTES[0]['q']} - {QUOTES[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{QUOTES[1]['q']} - {QUOTES[1]['a']}"
            "\n"
        )

        with patch(
            "zen_quotes.main.open", new=mock_open(read_data=read_data)
        ), patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=QUOTES_MODEL.quotes[1]),
        ):
            Quotes().run()
        self.assertEqual(mock_stdout.getvalue(), expected)


if __name__ == "__main__":
    unittest.main()
