import json
import logging
import pathlib
from datetime import date, timedelta

import pytest
import requests
from pydantic import ValidationError
from pytest_mock import MockerFixture

import zen_quotes.main


@pytest.fixture(name="quotes_list")
def quotes_list_fixture() -> list[dict[str, str]]:
    return [
        {
            "q": "A crisis is an opportunity riding the dangerous wind.",
            "a": "Chinese Proverb",
        },
        {
            "q": "Till it has loved, no man or woman can become itself.",
            "a": "Emily Dickinson",
        },
    ]


@pytest.fixture(name="quotes")
def quotes_fixture(quotes_list: list[dict[str, str]]) -> zen_quotes.main.Quotes:
    return zen_quotes.main.Quotes(
        last_update=date.today(),
        today=[
            zen_quotes.main.Quote(
                quote=quotes_list[0]["q"], author=quotes_list[0]["a"]
            )
        ],
        quotes=[
            zen_quotes.main.Quote(quote=quote["q"], author=quote["a"])
            for quote in quotes_list
        ],
    )


def test_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    quotes_list: list[dict[str, str]],
    quotes: zen_quotes.main.Quotes,
) -> None:
    monkeypatch.setattr(zen_quotes.main.QuotesStorage, "read", lambda: quotes)
    monkeypatch.setattr(
        zen_quotes.main, "choice", lambda list: quotes.quotes[1]
    )

    zen_quotes.main.main()

    assert capsys.readouterr().out == (
        "TODAY:\n"
        f"{quotes_list[0]['q']} - {quotes_list[0]['a']}\n"
        "\n"
        "RANDOM:\n"
        f"{quotes_list[1]['q']} - {quotes_list[1]['a']}"
        "\n"
    )


def test_quotes_manager_init_quotes_exist(
    monkeypatch: pytest.MonkeyPatch, quotes: zen_quotes.main.Quotes
) -> None:
    monkeypatch.setattr(zen_quotes.main.QuotesStorage, "read", lambda: quotes)

    assert zen_quotes.main.QuotesManager() is not None


def test_quotes_manager_init_quotes_none(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    monkeypatch.setattr(
        zen_quotes.main.QuotesStorage,
        "read",
        mocker.Mock(side_effect=FileNotFoundError),
    )

    assert zen_quotes.main.QuotesManager().quotes is None


def test_quotes_storage_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    quotes_list: list[dict[str, str]],
    quotes: zen_quotes.main.Quotes,
) -> None:
    output_dir = tmp_path / "output"
    output_file = output_dir / "zen_quotes.json"
    monkeypatch.setattr(
        zen_quotes.main.QuotesStorage, "_OUTPUT_DIR", output_dir
    )
    monkeypatch.setattr(
        zen_quotes.main.QuotesStorage, "_OUTPUT_FILE", output_file
    )

    zen_quotes.main.QuotesStorage.write(quotes)

    expected_json = {
        "last_update": str(date.today()),
        "today": [
            {
                "quote": quotes_list[0]["q"],
                "author": quotes_list[0]["a"],
            }
        ],
        "quotes": [
            {"quote": quote["q"], "author": quote["a"]} for quote in quotes_list
        ],
    }
    assert output_file.read_text(encoding="utf8") == json.dumps(
        expected_json, indent=4
    )


def test_quote_str(quotes_list: list[dict[str, str]]) -> None:
    result = str(
        zen_quotes.main.Quote(
            quote=quotes_list[0]["q"], author=quotes_list[0]["a"]
        )
    )
    assert result == f"{quotes_list[0]['q']} - {quotes_list[0]['a']}"


class TestQuotesManagerRun:
    @pytest.fixture(name="quotes_manager")
    def quotes_manager_fixture(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> zen_quotes.main.QuotesManager:
        monkeypatch.setattr(
            zen_quotes.main.QuotesStorage,
            "read",
            mocker.Mock(side_effect=FileNotFoundError),
        )

        return zen_quotes.main.QuotesManager()

    def test_pass(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        quotes_list: list[dict[str, str]],
        quotes: zen_quotes.main.Quotes,
        quotes_manager: zen_quotes.main.QuotesManager,
    ) -> None:
        mock_quotes_write = mocker.patch("zen_quotes.main.QuotesStorage.write")
        monkeypatch.setattr(
            zen_quotes.main,
            "request_quotes",
            mocker.Mock(side_effect=[quotes.today, quotes.quotes]),
        )
        monkeypatch.setattr(
            zen_quotes.main, "choice", lambda list: quotes.quotes[1]
        )

        quotes_manager.run()

        mock_quotes_write.assert_called_once_with(quotes)
        assert capsys.readouterr().out == (
            "Requesting new quotes\n"
            "TODAY:\n"
            f"{quotes_list[0]['q']} - {quotes_list[0]['a']}\n"
            "\n"
            "RANDOM:\n"
            f"{quotes_list[1]['q']} - {quotes_list[1]['a']}"
            "\n"
        )

    def test_no_update(
        self,
        mocker: MockerFixture,
        quotes: zen_quotes.main.Quotes,
        quotes_manager: zen_quotes.main.QuotesManager,
    ) -> None:
        mock_request_quotes = mocker.patch("zen_quotes.main.request_quotes")
        mock_quotes_write = mocker.patch("zen_quotes.main.QuotesStorage.write")
        mock_quotes_print = mocker.patch.object(quotes_manager, "_print")
        quotes_manager.quotes = quotes

        quotes_manager.run()

        mock_request_quotes.assert_not_called()
        mock_quotes_write.assert_not_called()
        mock_quotes_print.assert_called_once()

    def test_quotes_yesterday(
        self,
        mocker: MockerFixture,
        quotes: zen_quotes.main.Quotes,
        quotes_manager: zen_quotes.main.QuotesManager,
    ) -> None:
        mock_request_quotes = mocker.patch("zen_quotes.main.request_quotes")
        mock_quotes_write = mocker.patch("zen_quotes.main.QuotesStorage.write")
        mock_quotes_print = mocker.patch.object(quotes_manager, "_print")
        quotes_manager.quotes = quotes
        quotes_manager.quotes.last_update -= timedelta(days=1)

        quotes_manager.run()

        assert mock_request_quotes.call_count == 2
        mock_quotes_write.assert_called_once()
        mock_quotes_print.assert_called_once()

    def test_request_quotes_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        quotes_manager: zen_quotes.main.QuotesManager,
    ) -> None:
        mock_quotes_write = mocker.patch("zen_quotes.main.QuotesStorage.write")
        monkeypatch.setattr(
            zen_quotes.main,
            "request_quotes",
            mocker.Mock(side_effect=requests.ConnectionError),
        )

        quotes_manager.run()

        assert quotes_manager.quotes is None
        mock_quotes_write.assert_not_called()


class TestQuotesStorageRead:
    def test_pass(
        self,
        monkeypatch: pytest.MonkeyPatch,
        quotes: zen_quotes.main.Quotes,
    ) -> None:
        monkeypatch.setattr(
            pathlib.Path,
            "read_text",
            lambda *a, **k: quotes.model_dump_json(indent=4),
        )

        assert zen_quotes.main.QuotesStorage.read() == quotes

    def test_file_not_found(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ) -> None:
        monkeypatch.setattr(
            pathlib.Path,
            "read_text",
            mocker.Mock(side_effect=FileNotFoundError),
        )

        with pytest.raises(FileNotFoundError):
            zen_quotes.main.QuotesStorage.read()

        output_file = (
            pathlib.Path(__file__).parent.parent.parent
            / "output"
            / "zen_quotes.json"
        )
        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                f"Output file not found: {output_file.as_posix()}",
            )
        ]

    def test_invalid_json(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        quotes: zen_quotes.main.Quotes,
    ) -> None:
        file_content = quotes.model_dump_json(indent=4).replace(
            "today", "oday", 1
        )
        monkeypatch.setattr(
            pathlib.Path, "read_text", lambda *a, **k: file_content
        )

        with pytest.raises(ValidationError):
            zen_quotes.main.QuotesStorage.read()

        output_file = (
            pathlib.Path(__file__).parent.parent.parent
            / "output"
            / "zen_quotes.json"
        )
        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                f"Error parsing output file: {output_file.as_posix()}",
            )
        ]


class TestRequestQuotes:
    def test_quote_single(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        quotes_list: list[dict[str, str]],
    ) -> None:
        mock_response = mocker.Mock()
        mock_response.json = mocker.Mock(return_value=[quotes_list[0]])
        monkeypatch.setattr(requests, "get", lambda *a, **k: mock_response)

        result = zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.TODAY)
        assert result == [
            zen_quotes.main.Quote(
                quote=quotes_list[0]["q"],
                author=quotes_list[0]["a"],
            )
        ]

    def test_quote_multiple(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        quotes_list: list[dict[str, str]],
        quotes: zen_quotes.main.Quotes,
    ) -> None:
        mock_response = mocker.Mock()
        mock_response.json = mocker.Mock(return_value=quotes_list)
        monkeypatch.setattr(requests, "get", lambda *a, **k: mock_response)

        assert (
            zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.QUOTES)
            == quotes.quotes
        )

    def test_connection_error(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ) -> None:
        monkeypatch.setattr(
            requests, "get", mocker.Mock(side_effect=requests.ConnectionError)
        )

        with pytest.raises(requests.ConnectionError):
            zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.QUOTES)

        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                (
                    "ConnectionError when requesting Zen Quotes: "
                    "https://zenquotes.io/api/quotes"
                ),
            )
        ]

    def test_http_error(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        response = requests.Response()
        response.status_code = 400
        monkeypatch.setattr(requests, "get", lambda *a, **k: response)

        with pytest.raises(requests.HTTPError):
            zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.QUOTES)

        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                "Invalid HTTP status code: https://zenquotes.io/api/quotes",
            )
        ]

    def test_json_decode_error(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ) -> None:
        response = requests.Response()
        mocker.patch.object(response, "raise_for_status")
        monkeypatch.setattr(requests, "get", lambda *a, **k: response)

        with pytest.raises(requests.exceptions.JSONDecodeError):
            zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.QUOTES)

        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                (
                    "Invalid JSON content in response: "
                    "https://zenquotes.io/api/quotes"
                ),
            )
        ]

    def test_key_error(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        quotes_list: list[dict[str, str]],
    ) -> None:
        del quotes_list[0]["q"]
        mock_response = mocker.Mock()
        mock_response.json = mocker.Mock(return_value=quotes_list)
        monkeypatch.setattr(requests, "get", lambda *a, **k: mock_response)

        with pytest.raises(KeyError):
            zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.QUOTES)

        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                "Key missing in JSON content: https://zenquotes.io/api/quotes",
            )
        ]

    def test_timeout(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ) -> None:
        monkeypatch.setattr(
            requests, "get", mocker.Mock(side_effect=requests.Timeout)
        )

        with pytest.raises(requests.Timeout):
            zen_quotes.main.request_quotes(zen_quotes.main.QuoteMode.QUOTES)

        assert caplog.record_tuples == [
            (
                "zen_quotes.main",
                logging.WARNING,
                (
                    "Timeout when requesting Zen Quotes: "
                    "https://zenquotes.io/api/quotes"
                ),
            )
        ]
