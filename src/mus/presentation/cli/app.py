"""Main entrypoint for the MUS command-line interface."""

import typer

from mus.presentation.cli.pipeline import app as pipeline_app
from mus.presentation.cli.render import app as render_app
from mus.presentation.cli.transcribe import app as transcribe_app
from mus.presentation.cli.voice import app as voice_app

app = typer.Typer(
    name="mus",
    help="MUS: Source-Filter Vocal Decomposition, Modulation and Musical Resynthesis.",
    no_args_is_help=True,
)

app.add_typer(voice_app, name="voice")
app.add_typer(transcribe_app, name="transcribe")
app.add_typer(render_app, name="render")
app.add_typer(pipeline_app, name="pipeline")


def main() -> None:
    """CLI execution entrypoint."""
    app()


if __name__ == "__main__":
    main()
