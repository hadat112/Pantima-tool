"""CLI entry point for text-converter tools."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="tc", help="Bulk text-to-file conversion tools.", no_args_is_help=True)
email_app = typer.Typer(help="Convert plain-text emails to .eml files.", no_args_is_help=True)
note_app = typer.Typer(help="Convert notes to .txt files.", no_args_is_help=True)
message_app = typer.Typer(help="Convert messages to .txt files.", no_args_is_help=True)
audio_app = typer.Typer(help="Convert voicemail/audio transcripts to .txt files.", no_args_is_help=True)
app.add_typer(email_app, name="email")
app.add_typer(note_app, name="note")
app.add_typer(message_app, name="message")
app.add_typer(audio_app, name="audio")

console = Console()


@email_app.command("convert")
def email_convert(
    input_file: Path = typer.Argument(..., help="Plain-text email file (.txt)"),
    output: Path = typer.Argument(..., help="Output .eml file path"),
):
    """Convert a single plain-text email file to .eml."""
    from text_converter.email_to_eml import from_text

    if not input_file.exists():
        console.print(f"[red]File not found:[/red] {input_file}")
        raise typer.Exit(1)

    text = input_file.read_text(encoding="utf-8")
    out = from_text(text, output)
    console.print(f"[green]✓[/green] {out}")


@email_app.command("batch")
def email_batch(
    input_dir: Path = typer.Argument(..., help="Directory with .txt email files"),
    output_dir: Path = typer.Argument(..., help="Directory to write .eml files"),
    glob: str = typer.Option("*.txt", "--glob", "-g", help="File pattern to match"),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
):
    """Convert all plain-text email files in a directory to .eml."""
    from text_converter.email_to_eml import batch_from_dir

    if not input_dir.is_dir():
        console.print(f"[red]Not a directory:[/red] {input_dir}")
        raise typer.Exit(1)

    results = batch_from_dir(input_dir, output_dir, glob=glob, max_workers=workers)

    table = Table(title=f"Converted {len(results)} file(s)")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for r in results:
        table.add_row(r.name, f"{r.stat().st_size} B")

    console.print(table)


@email_app.command("from-csv")
def email_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with email scripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write .eml files"),
    category_col: str = typer.Option("Data type/category", "--cat-col", help="Category column name"),
    scrip_col: str = typer.Option("Scrip", "--scrip-col", help="Script column name"),
    category_prefix: list[str] = typer.Option([], "--prefix", "-p", help="Filter by prefix (repeat for multiple). Omit = all rows."),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process per run (0 = all)"),
):
    """Convert rows from a CSV file to .eml files.

    By default converts ALL rows with a Scrip value.
    Use --prefix to filter by category, e.g. --prefix Mail_Contact --prefix Message_contact.
    """
    from text_converter.email_to_eml import batch_from_csv

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    results = batch_from_csv(
        csv_path=csv_file,
        output_dir=output_dir,
        category_col=category_col,
        scrip_col=scrip_col,
        category_prefix=category_prefix or None,
        max_workers=workers,
        limit=limit,
    )

    if not results:
        console.print("[yellow]No matching rows found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Converted {len(results)} email(s) → {output_dir}")
    table.add_column("Category", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for category, path in results:
        table.add_row(category, path.name, f"{path.stat().st_size} B")

    console.print(table)


@note_app.command("from-csv")
def note_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with note scripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write .txt files"),
    script_col: str = typer.Option("Script", "--script-col", help="Script column name"),
    participant_col: str = typer.Option("participant", "--participant-col", help="Participant column name"),
    date_col: str = typer.Option("Date", "--date-col", help="Date column name"),
    occupation_col: str = typer.Option("occupation", "--occupation-col", help="Occupation column (used as tag)"),
    category_col: str = typer.Option("primary category", "--category-col", help="Category column (used as tag)"),
    data_type_col: str = typer.Option("Data_type", "--type-col", help="Data type column for filtering"),
    data_type_filter: str = typer.Option("", "--type", "-t", help="Filter by data type value (e.g. Note). Empty = all rows."),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process per run (0 = all)"),
):
    """Convert Script column in a CSV to individual .txt note files."""
    from text_converter.note_to_txt import batch_from_csv

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    results = batch_from_csv(
        csv_path=csv_file,
        output_dir=output_dir,
        script_col=script_col,
        participant_col=participant_col,
        date_col=date_col,
        occupation_col=occupation_col,
        category_col=category_col,
        data_type_col=data_type_col,
        data_type_filter=data_type_filter or None,
        max_workers=workers,
        limit=limit,
    )

    if not results:
        console.print("[yellow]No rows found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Converted {len(results)} note(s) → {output_dir}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for i, path in enumerate(results, 1):
        table.add_row(str(i), path.name, f"{path.stat().st_size} B")

    console.print(table)


def _csv_from_options(
    app_name: str,
    csv_file: Path,
    output_dir: Path,
    script_col: str,
    participant_col: str,
    data_type_col: str,
    data_type_filter: str,
    batch_fn,
    workers: int = 1,
    limit: int = 0,
) -> None:
    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    results = batch_fn(
        csv_path=csv_file,
        output_dir=output_dir,
        script_col=script_col,
        participant_col=participant_col,
        data_type_col=data_type_col,
        data_type_filter=data_type_filter or None,
        max_workers=workers,
        limit=limit,
    )

    if not results:
        console.print("[yellow]No rows found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Converted {len(results)} {app_name}(s) → {output_dir}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for i, path in enumerate(results, 1):
        table.add_row(str(i), path.name, f"{path.stat().st_size} B")
    console.print(table)


@message_app.command("from-csv")
def message_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with message scripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write .txt files"),
    script_col: str = typer.Option("Script", "--script-col"),
    participant_col: str = typer.Option("participant", "--participant-col"),
    data_type_col: str = typer.Option("Data_type", "--type-col"),
    data_type_filter: str = typer.Option("", "--type", "-t", help="Filter by data type value. Empty = all rows."),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process per run (0 = all)"),
):
    """Convert message Script rows in a CSV to individual .txt files."""
    from text_converter.message_to_txt import batch_from_csv
    _csv_from_options("message", csv_file, output_dir, script_col, participant_col, data_type_col, data_type_filter, batch_from_csv, workers, limit)


@audio_app.command("from-csv")
def audio_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with voicemail/audio transcripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write .txt files"),
    script_col: str = typer.Option("Script", "--script-col"),
    participant_col: str = typer.Option("participant", "--participant-col"),
    data_type_col: str = typer.Option("Data_type", "--type-col"),
    data_type_filter: str = typer.Option("", "--type", "-t", help="Filter by data type value. Empty = all rows."),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process per run (0 = all)"),
):
    """Convert voicemail/audio transcript rows in a CSV to individual .txt files."""
    from text_converter.audio_to_text import batch_from_csv
    _csv_from_options("transcript", csv_file, output_dir, script_col, participant_col, data_type_col, data_type_filter, batch_from_csv, workers, limit)


def main():
    app()
