"""Main entrypoint for the MUS command-line interface."""

from pathlib import Path

import typer

from mus.presentation.cli.pipeline import app as pipeline_app
from mus.presentation.cli.render import app as render_app
from mus.presentation.cli.transcribe import app as transcribe_app
from mus.presentation.cli.voice import app as voice_app
from mus.stem_separation.infrastructure.cookie_extractor import (
    export_cookies_auto,
    export_cookies_from_browser,
    has_valid_auth_cookies,
)

app = typer.Typer(
    name="mus",
    help="MUS: Source-Filter Vocal Decomposition, Modulation and Musical Resynthesis.",
    no_args_is_help=True,
)

app.add_typer(voice_app, name="voice")
app.add_typer(transcribe_app, name="transcribe")
app.add_typer(render_app, name="render")
app.add_typer(pipeline_app, name="pipeline")


@app.command(name="export-cookies")
def export_cookies_cmd(
    browser: str = typer.Option("firefox", "--browser", "-b", help="Browser to extract from."),
    output: Path = typer.Option(
        Path("./data/cookies.txt"), "--out", "-o", help="Target cookie file path."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-extraction even if valid cookies exist."
    ),
) -> None:
    """Export YouTube session authentication cookies from browser."""
    resolved_out = output.resolve()
    if not force and has_valid_auth_cookies(resolved_out):
        typer.echo(f"Valid cookies already exist at {resolved_out}. Use --force to re-extract.")
        return

    success = export_cookies_from_browser(
        browser=browser, output_file=resolved_out, require_auth=True
    )
    if not success:
        success = export_cookies_auto(output_file=resolved_out, preferred_browser=browser)

    if success:
        typer.echo(f"✓ Successfully exported YouTube cookies to {resolved_out}")
    else:
        err_msg = f"✗ Failed extracting YouTube cookies from '{browser}'. Ensure you are logged in."
        typer.echo(err_msg, err=True)
        raise typer.Exit(code=1)


def main() -> None:
    """CLI execution entrypoint."""
    app()


if __name__ == "__main__":
    main()
