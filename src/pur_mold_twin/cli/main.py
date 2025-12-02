"""Typer application factory for the PUR-MOLD-TWIN CLI."""

from __future__ import annotations

import importlib.metadata as metadata

import typer

from .commands import register_commands
from ..utils import configure_logging

APP_NAME = "pur-mold-twin"


def _determine_version() -> str:
    try:
        return metadata.version(APP_NAME)
    except metadata.PackageNotFoundError:  # pragma: no cover - lokalne uruchomienia bez instalacji
        return "0.0.0+local"


def create_app() -> typer.Typer:
    """Create and configure the Typer CLI application."""

    app = typer.Typer(
        add_completion=False,
        context_settings={"help_option_names": ["-h", "--help"]},
        help="CLI for the PUR-MOLD-TWIN simulator (run-sim, optimize).",
    )
    register_commands(app)

    @app.callback()
    def _main_callback(
        version: bool = typer.Option(False, "--version", help="Show CLI version and exit."),
        verbose: bool = typer.Option(False, "--verbose", help="Enable verbose (DEBUG) logging."),
    ) -> None:
        level = "DEBUG" if verbose else "INFO"
        configure_logging(level)
        if version:
            typer.echo(f"{APP_NAME} CLI { _determine_version() }")
            raise typer.Exit()

    return app


app = create_app()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
