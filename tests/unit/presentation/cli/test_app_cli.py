"""Unit tests for top-level MUS CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from mus.presentation.cli.app import app

runner = CliRunner()


def test_export_cookies_cli_skips_when_valid_without_force(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    with patch(
        "mus.presentation.cli.app.has_valid_auth_cookies",
        return_value=True,
    ):
        result = runner.invoke(app, ["export-cookies", "--out", str(cookie_file)])
        assert result.exit_code == 0
        assert "Valid cookies already exist" in result.output


def test_export_cookies_cli_triggers_export(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    with (
        patch(
            "mus.presentation.cli.app.has_valid_auth_cookies",
            return_value=False,
        ),
        patch(
            "mus.presentation.cli.app.export_cookies_from_browser",
            return_value=True,
        ) as mock_export,
    ):
        result = runner.invoke(
            app, ["export-cookies", "--out", str(cookie_file), "--browser", "firefox"]
        )
        assert result.exit_code == 0
        assert "Successfully exported" in result.output
        mock_export.assert_called_once()
