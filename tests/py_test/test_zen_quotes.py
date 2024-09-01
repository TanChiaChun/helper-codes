import copy
import json
import logging
import tempfile
import unittest
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from pydantic import ValidationError

from zen_quotes.main import (
    Quote,
    QuoteMode,
    Quotes,
    QuotesModel,
    QuotesStorage,
    logger,
)

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
QUOTES_MODEL_JSON_STR = QUOTES_MODEL.model_dump_json(indent=4)


class TestQuote(unittest.TestCase):
    def test_str(self) -> None:
        self.assertEqual(
            str(Quote(quote=QUOTES[0]["q"], author=QUOTES[0]["a"])),
            f"{QUOTES[0]['q']} - {QUOTES[0]['a']}",
        )


class TestQuotesStorage(unittest.TestCase):
    def test_write(self) -> None:
        expected = {
            "last_update": str(date.today()),
            "today": [{"quote": QUOTES[0]["q"], "author": QUOTES[0]["a"]}],
            "quotes": [
                {"quote": quote["q"], "author": quote["a"]} for quote in QUOTES
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdirname:
            output_dir = Path(tmpdirname)
            output_file = output_dir / "zen_quotes.json"

            with patch.multiple(
                QuotesStorage, _OUTPUT_DIR=output_dir, _OUTPUT_FILE=output_file
            ):
                QuotesStorage.write(QUOTES_MODEL)

            self.assertEqual(
                output_file.read_text(encoding="utf8"),
                json.dumps(expected, indent=4),
            )


class TestQuotesStorageRead(unittest.TestCase):
    def test_pass(self) -> None:
        with patch(
            "pathlib.Path.read_text",
            new=Mock(return_value=QUOTES_MODEL_JSON_STR),
        ):
            quotes = QuotesStorage.read()
        self.assertEqual(
            quotes.model_dump_json(indent=4), QUOTES_MODEL_JSON_STR
        )

    def test_file_not_found(self) -> None:
        with patch(
            "pathlib.Path.read_text",
            new=Mock(side_effect=FileNotFoundError),
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            with self.assertRaises(FileNotFoundError):
                QuotesStorage.read()

            output_file = (
                Path(__file__).parent.parent.parent
                / "output"
                / "zen_quotes.json"
            )
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                f"Output file not found: {output_file.as_posix()}",
            )

    def test_invalid_json(self) -> None:
        read_data = QUOTES_MODEL_JSON_STR
        read_data = read_data.replace("today", "oday", 1)

        with patch(
            "pathlib.Path.read_text", new=Mock(return_value=read_data)
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            with self.assertRaises(ValidationError):
                QuotesStorage.read()

            output_file = (
                Path(__file__).parent.parent.parent
                / "output"
                / "zen_quotes.json"
            )
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                f"Error parsing output file: {output_file.as_posix()}",
            )


class TestQuotes(unittest.TestCase):
    def setUp(self) -> None:
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(side_effect=FileNotFoundError),
        ):
            self.quotes = Quotes()

    @patch(
        "zen_quotes.main.QuotesStorage.read",
        new=Mock(return_value=QUOTES_MODEL),
    )
    def test_init_quotes_exist(self) -> None:
        self.assertIsNotNone(Quotes().quotes)

    @patch(
        "zen_quotes.main.QuotesStorage.read",
        new=Mock(side_effect=FileNotFoundError),
    )
    def test_init_quotes_none(self) -> None:
        self.assertIsNone(Quotes().quotes)

    def test_is_update_required_false(self) -> None:
        self.quotes.quotes = QUOTES_MODEL
        self.assertIs(self.quotes.is_update_required(), False)

    def test_is_update_required_true_empty_quotes(self) -> None:
        self.assertIs(self.quotes.is_update_required(), True)

    def test_is_update_required_true_outdated(self) -> None:
        self.quotes.quotes = copy.copy(QUOTES_MODEL)
        self.quotes.quotes.last_update -= timedelta(days=1)
        self.assertIs(self.quotes.is_update_required(), True)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print(self, mock_stdout: StringIO) -> None:
        self.quotes.quotes = QUOTES_MODEL

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
            new=Mock(return_value=self.quotes.quotes.quotes[1]),
        ):
            self.quotes.print()
        self.assertEqual(mock_stdout.getvalue(), expected)

    @patch("sys.stdout", new_callable=StringIO)
    def test_run_print_only(self, mock_stdout: StringIO) -> None:
        with patch.object(self.quotes, "request", new=Mock(return_value=None)):
            self.quotes.run()
        self.assertEqual(mock_stdout.getvalue(), "Requesting new quotes\n")


class TestQuotesRequest(unittest.TestCase):
    def setUp(self) -> None:
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(side_effect=FileNotFoundError),
        ):
            self.quotes = Quotes()

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
                self.quotes.request(QuoteMode.TODAY),
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
                self.quotes.request(QuoteMode.QUOTES),
                QUOTES_MODEL.quotes,
            )

    def test_request_quote_connection_error(self) -> None:
        with patch(
            "requests.get", new=Mock(side_effect=requests.ConnectionError)
        ), self.assertLogs(logger, logging.WARNING) as logger_obj:
            self.assertIsNone(self.quotes.request(QuoteMode.QUOTES))
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
            self.assertIsNone(self.quotes.request(QuoteMode.QUOTES))
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
            self.assertIsNone(self.quotes.request(QuoteMode.QUOTES))
            self.assertEqual(
                logger_obj.records[0].getMessage(),
                "Invalid HTTP status code: https://zenquotes.io/api/quotes",
            )


class TestModule(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_main(self, mock_stdout: StringIO) -> None:
        expected = (
            "TODAY:\n"
            f"{QUOTES[0]['q']} - {QUOTES[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{QUOTES[1]['q']} - {QUOTES[1]['a']}"
            "\n"
        )

        with patch(
            "pathlib.Path.read_text",
            new=Mock(return_value=QUOTES_MODEL_JSON_STR),
        ), patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=QUOTES_MODEL.quotes[1]),
        ):
            Quotes().run()
        self.assertEqual(mock_stdout.getvalue(), expected)


if __name__ == "__main__":
    unittest.main()
