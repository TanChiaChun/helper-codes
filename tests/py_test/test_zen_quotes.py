import json
import logging
import tempfile
import unittest
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import requests
from pydantic import ValidationError

from zen_quotes.main import (
    Quote,
    QuoteMode,
    Quotes,
    QuotesManager,
    QuotesStorage,
    logger,
    main,
    request_quotes,
)


class BaseFixtureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.quotes_list = [
            {
                "q": "A crisis is an opportunity riding the dangerous wind.",
                "a": "Chinese Proverb",
            },
            {
                "q": "Till it has loved, no man or woman can become itself.",
                "a": "Emily Dickinson",
            },
        ]
        self.quotes = Quotes(
            last_update=date.today(),
            today=[
                Quote(
                    quote=self.quotes_list[0]["q"],
                    author=self.quotes_list[0]["a"],
                )
            ],
            quotes=[
                Quote(quote=quote["q"], author=quote["a"])
                for quote in self.quotes_list
            ],
        )
        self.quotes_model_json_str = self.quotes.model_dump_json(indent=4)


class QuotesManagerFixtureTestCase(BaseFixtureTestCase):
    def setUp(self) -> None:
        super().setUp()
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(side_effect=FileNotFoundError),
        ):
            self.quotes_manager = QuotesManager()


class TestModule(BaseFixtureTestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_main(self, mock_stdout: StringIO) -> None:
        expected = (
            "TODAY:\n"
            f"{self.quotes_list[0]['q']} - {self.quotes_list[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{self.quotes_list[1]['q']} - {self.quotes_list[1]['a']}"
            "\n"
        )

        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(return_value=self.quotes),
        ), patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=self.quotes.quotes[1]),
        ):
            main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestQuote(BaseFixtureTestCase):
    def test_str(self) -> None:
        self.assertEqual(
            str(
                Quote(
                    quote=self.quotes_list[0]["q"],
                    author=self.quotes_list[0]["a"],
                )
            ),
            f"{self.quotes_list[0]['q']} - {self.quotes_list[0]['a']}",
        )


class TestQuotesManager(BaseFixtureTestCase):
    def test_init_quotes_exist(self) -> None:
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(return_value=self.quotes),
        ):
            self.assertIsNotNone(QuotesManager().quotes)

    def test_init_quotes_none(self) -> None:
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(side_effect=FileNotFoundError),
        ):
            self.assertIsNone(QuotesManager().quotes)


class TestQuotesManagerRun(QuotesManagerFixtureTestCase):
    @patch("sys.stdout", new_callable=StringIO)
    @patch("zen_quotes.main.QuotesStorage.write")
    def test_pass(
        self, mock_quotes_write: MagicMock, mock_stdout: StringIO
    ) -> None:
        mock_quotes_requests = Mock(
            side_effect=[self.quotes.today, self.quotes.quotes]
        )
        with patch(
            "zen_quotes.main.request_quotes", new=mock_quotes_requests
        ), patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=self.quotes.quotes[1]),
        ):
            self.quotes_manager.run()

        mock_quotes_write.assert_called_once_with(self.quotes)

        expected = (
            "Requesting new quotes\n"
            "TODAY:\n"
            f"{self.quotes_list[0]['q']} - {self.quotes_list[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{self.quotes_list[1]['q']} - {self.quotes_list[1]['a']}"
            "\n"
        )
        self.assertEqual(mock_stdout.getvalue(), expected)

    @patch("zen_quotes.main.QuotesStorage.write")
    @patch("zen_quotes.main.request_quotes")
    def test_quotes_yesterday(
        self, mock_quotes_request: MagicMock, mock_quotes_write: MagicMock
    ) -> None:
        self.quotes_manager.quotes = self.quotes
        self.quotes_manager.quotes.last_update -= timedelta(days=1)

        with patch.object(self.quotes_manager, "_print") as mock_quotes_print:
            self.quotes_manager.run()

            mock_quotes_print.assert_called_once()

        self.assertEqual(mock_quotes_request.call_count, 2)
        mock_quotes_write.assert_called_once()

    @patch("zen_quotes.main.QuotesStorage.write")
    def test_request_quotes_error(self, mock_quotes_write: MagicMock) -> None:
        with patch(
            "zen_quotes.main.request_quotes",
            new=Mock(side_effect=requests.ConnectionError),
        ):
            self.quotes_manager.run()

        self.assertIsNone(self.quotes_manager.quotes)
        mock_quotes_write.assert_not_called()

    @patch("zen_quotes.main.QuotesStorage.write")
    @patch("zen_quotes.main.request_quotes")
    def test_no_update(
        self, mock_quotes_request: MagicMock, mock_quotes_write: MagicMock
    ) -> None:
        self.quotes_manager.quotes = self.quotes

        with patch.object(self.quotes_manager, "_print") as mock_quotes_print:
            self.quotes_manager.run()

            mock_quotes_print.assert_called_once()

            mock_quotes_request.assert_not_called()

        mock_quotes_write.assert_not_called()


class TestQuotesStorage(BaseFixtureTestCase):
    def test_write(self) -> None:
        expected_json = {
            "last_update": str(date.today()),
            "today": [
                {
                    "quote": self.quotes_list[0]["q"],
                    "author": self.quotes_list[0]["a"],
                }
            ],
            "quotes": [
                {"quote": quote["q"], "author": quote["a"]}
                for quote in self.quotes_list
            ],
        }
        expected = json.dumps(expected_json, indent=4)

        with tempfile.TemporaryDirectory() as tmpdirname:
            output_dir = Path(tmpdirname) / "output"
            output_file = output_dir / "zen_quotes.json"

            with patch.multiple(
                QuotesStorage, _OUTPUT_DIR=output_dir, _OUTPUT_FILE=output_file
            ):
                QuotesStorage.write(self.quotes)

            self.assertEqual(output_file.read_text(encoding="utf8"), expected)


class TestQuotesStorageRead(BaseFixtureTestCase):
    def test_pass(self) -> None:
        with patch(
            "pathlib.Path.read_text",
            new=Mock(return_value=self.quotes_model_json_str),
        ):
            quotes = QuotesStorage.read()
        self.assertEqual(quotes, self.quotes)

    def test_file_not_found(self) -> None:
        with patch(
            "pathlib.Path.read_text",
            new=Mock(side_effect=FileNotFoundError),
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(FileNotFoundError):
                QuotesStorage.read()

            output_file = (
                Path(__file__).parent.parent.parent
                / "output"
                / "zen_quotes.json"
            )
            self.assertEqual(
                cm.records[0].getMessage(),
                f"Output file not found: {output_file.as_posix()}",
            )

    def test_invalid_json(self) -> None:
        read_data = self.quotes_model_json_str.replace("today", "oday", 1)

        with patch(
            "pathlib.Path.read_text", new=Mock(return_value=read_data)
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(ValidationError):
                QuotesStorage.read()

            output_file = (
                Path(__file__).parent.parent.parent
                / "output"
                / "zen_quotes.json"
            )
            self.assertEqual(
                cm.records[0].getMessage(),
                f"Error parsing output file: {output_file.as_posix()}",
            )


class TestRequestQuotes(BaseFixtureTestCase):
    def test_quote_single(self) -> None:
        mock_response = Mock()
        mock_response.json = Mock(return_value=[self.quotes_list[0]])

        with patch("requests.get", new=Mock(return_value=mock_response)):
            self.assertEqual(
                request_quotes(QuoteMode.TODAY),
                [
                    Quote(
                        quote=self.quotes_list[0]["q"],
                        author=self.quotes_list[0]["a"],
                    )
                ],
            )

    def test_quote_multiple(self) -> None:
        mock_response = Mock()
        mock_response.json = Mock(return_value=self.quotes_list)

        with patch("requests.get", new=Mock(return_value=mock_response)):
            self.assertEqual(
                request_quotes(QuoteMode.QUOTES),
                self.quotes.quotes,
            )

    def test_connection_error(self) -> None:
        with patch(
            "requests.get", new=Mock(side_effect=requests.ConnectionError)
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(requests.ConnectionError):
                request_quotes(QuoteMode.QUOTES)
            self.assertEqual(
                cm.records[0].getMessage(),
                (
                    "ConnectionError when requesting Zen Quotes: "
                    "https://zenquotes.io/api/quotes"
                ),
            )

    def test_timeout(self) -> None:
        with patch(
            "requests.get", new=Mock(side_effect=requests.Timeout)
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(requests.Timeout):
                request_quotes(QuoteMode.QUOTES)
            self.assertEqual(
                cm.records[0].getMessage(),
                (
                    "Timeout when requesting Zen Quotes: "
                    "https://zenquotes.io/api/quotes"
                ),
            )

    def test_http_error(self) -> None:
        response = requests.Response()
        response.status_code = 400

        with patch(
            "requests.get", new=Mock(return_value=response)
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(requests.HTTPError):
                request_quotes(QuoteMode.QUOTES)
            self.assertEqual(
                cm.records[0].getMessage(),
                "Invalid HTTP status code: https://zenquotes.io/api/quotes",
            )

    def test_json_decode_error(self) -> None:
        response = requests.Response()

        with patch.object(response, "raise_for_status"), patch(
            "requests.get", new=Mock(return_value=response)
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(requests.exceptions.JSONDecodeError):
                request_quotes(QuoteMode.QUOTES)
            self.assertEqual(
                cm.records[0].getMessage(),
                (
                    "Invalid JSON content in response: "
                    "https://zenquotes.io/api/quotes"
                ),
            )

    def test_key_error(self) -> None:
        del self.quotes_list[0]["q"]
        mock_response = Mock()
        mock_response.json = Mock(return_value=self.quotes_list)

        with patch(
            "requests.get", new=Mock(return_value=mock_response)
        ), self.assertLogs(logger=logger, level=logging.WARNING) as cm:
            with self.assertRaises(KeyError):
                request_quotes(QuoteMode.QUOTES)
            self.assertEqual(
                cm.records[0].getMessage(),
                "Key missing in JSON content: https://zenquotes.io/api/quotes",
            )


if __name__ == "__main__":
    unittest.main()
