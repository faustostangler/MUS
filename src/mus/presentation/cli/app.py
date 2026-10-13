"""Main entrypoint for the MUS command-line interface."""

import typer

from mus.presentation.cli.voice import app as voice_app

app = typer.Typer(
    name="mus",
    help="MUS: Source-Filter Vocal Decomposition, Modulation and Musical Resynthesis.",
    no_args_is_help=True,
)

app.add_typer(voice_app, name="voice")


def main() -> None:
    """CLI execution entrypoint."""
    app()


if __name__ == "__main__":
    main()
