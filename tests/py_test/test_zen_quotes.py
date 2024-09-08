import json
import logging
import tempfile
import unittest
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import DEFAULT, MagicMock, Mock, patch

import requests
from pydantic import ValidationError

from zen_quotes.main import (
    Quote,
    QuoteMode,
    Quotes,
    QuotesModel,
    QuotesStorage,
    logger,
    main,
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
        self.quotes_model = QuotesModel(
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
        self.quotes_model_json_str = self.quotes_model.model_dump_json(indent=4)


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


class TestQuotesStorage(BaseFixtureTestCase):
    def test_write(self) -> None:
        expected = {
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

        with tempfile.TemporaryDirectory() as tmpdirname:
            output_dir = Path(tmpdirname)
            output_file = output_dir / "zen_quotes.json"

            with patch.multiple(
                QuotesStorage, _OUTPUT_DIR=output_dir, _OUTPUT_FILE=output_file
            ):
                QuotesStorage.write(self.quotes_model)

            self.assertEqual(
                output_file.read_text(encoding="utf8"),
                json.dumps(expected, indent=4),
            )


class TestQuotesStorageRead(BaseFixtureTestCase):
    def test_pass(self) -> None:
        with patch(
            "pathlib.Path.read_text",
            new=Mock(return_value=self.quotes_model_json_str),
        ):
            quotes = QuotesStorage.read()
        self.assertEqual(
            quotes.model_dump_json(indent=4), self.quotes_model_json_str
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
        read_data = self.quotes_model_json_str.replace("today", "oday", 1)

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


class TestQuotes(BaseFixtureTestCase):
    def setUp(self) -> None:
        super().setUp()
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(side_effect=FileNotFoundError),
        ):
            self.quotes = Quotes()

    def test_init_quotes_exist(self) -> None:
        with patch(
            "zen_quotes.main.QuotesStorage.read",
            new=Mock(return_value=self.quotes_model),
        ):
            self.assertIsNotNone(Quotes().quotes)

    @patch(
        "zen_quotes.main.QuotesStorage.read",
        new=Mock(side_effect=FileNotFoundError),
    )
    def test_init_quotes_none(self) -> None:
        self.assertIsNone(Quotes().quotes)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print(self, mock_stdout: StringIO) -> None:
        self.quotes.quotes = self.quotes_model

        expected = (
            "TODAY:\n"
            f"{self.quotes_list[0]['q']} - {self.quotes_list[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{self.quotes_list[1]['q']} - {self.quotes_list[1]['a']}"
            "\n"
        )
        with patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=self.quotes.quotes.quotes[1]),
        ):
            self.quotes.print()
        self.assertEqual(mock_stdout.getvalue(), expected)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("zen_quotes.main.QuotesStorage.write")
    def test_run(
        self, mock_quotes_write: MagicMock, mock_stdout: StringIO
    ) -> None:
        mock_quotes_requests = Mock(
            side_effect=[self.quotes_model.today, self.quotes_model.quotes]
        )
        with patch.multiple(
            self.quotes, request=mock_quotes_requests, print=DEFAULT
        ) as mocks:
            self.quotes.run()

            mock_quotes_print: MagicMock = mocks["print"]
            mock_quotes_print.assert_called_once()

        mock_quotes_write.assert_called_once_with(self.quotes_model)

        self.assertEqual(
            mock_stdout.getvalue().split("\n")[0], "Requesting new quotes"
        )

    @patch("zen_quotes.main.QuotesStorage.write")
    def test_run_update_quotes_yesterday(
        self, mock_quotes_write: MagicMock
    ) -> None:
        self.quotes.quotes = self.quotes_model
        self.quotes.quotes.last_update -= timedelta(days=1)

        with patch.multiple(
            self.quotes, request=DEFAULT, print=DEFAULT
        ) as mocks:
            self.quotes.run()

            mock_quotes_request: MagicMock = mocks["request"]
            self.assertEqual(mock_quotes_request.call_count, 2)

            mock_quotes_print: MagicMock = mocks["print"]
            mock_quotes_print.assert_called_once()

        mock_quotes_write.assert_called_once()

    @patch("zen_quotes.main.QuotesStorage.write")
    def test_run_no_update(self, mock_quotes_write: MagicMock) -> None:
        self.quotes.quotes = self.quotes_model

        with patch.multiple(
            self.quotes, print=DEFAULT, request=DEFAULT
        ) as mocks:
            self.quotes.run()

            mock_quotes_print: MagicMock = mocks["print"]
            mock_quotes_print.assert_called_once()

            mock_quotes_request: MagicMock = mocks["request"]
            mock_quotes_request.assert_not_called()

        mock_quotes_write.assert_not_called()


class TestQuotesRequest(BaseFixtureTestCase):
    def setUp(self) -> None:
        super().setUp()
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
                    status_code=200,
                    json=Mock(return_value=[self.quotes_list[0]]),
                )
            ),
        ):
            self.assertEqual(
                self.quotes.request(QuoteMode.TODAY),
                [
                    Quote(
                        quote=self.quotes_list[0]["q"],
                        author=self.quotes_list[0]["a"],
                    )
                ],
            )

    def test_request_quote_multiple(self) -> None:
        with patch(
            "requests.get",
            new=Mock(
                return_value=Mock(
                    status_code=200, json=Mock(return_value=self.quotes_list)
                )
            ),
        ):
            self.assertEqual(
                self.quotes.request(QuoteMode.QUOTES),
                self.quotes_model.quotes,
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
            new=Mock(return_value=self.quotes_model),
        ), patch(
            "zen_quotes.main.choice",
            new=Mock(return_value=self.quotes_model.quotes[1]),
        ):
            main()
        self.assertEqual(mock_stdout.getvalue(), expected)


if __name__ == "__main__":
    unittest.main()
