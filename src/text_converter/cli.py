"""CLI entry point for text-converter tools."""

import typer
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="tc", help="Bulk text-to-file conversion tools.", no_args_is_help=True)
email_app = typer.Typer(help="Convert plain-text emails to .eml files.", no_args_is_help=True)
note_app = typer.Typer(help="Convert notes to .txt files.", no_args_is_help=True)
message_app = typer.Typer(help="Convert messages to .txt files.", no_args_is_help=True)
audio_app = typer.Typer(help="Convert voicemail/audio transcripts to .txt files.", no_args_is_help=True)
csv_app = typer.Typer(help="CSV utilities.", no_args_is_help=True)
chat_app  = typer.Typer(help="Generate mock chat screenshots (PNG) from CSV scripts.", no_args_is_help=True)
app.add_typer(email_app, name="email")
app.add_typer(note_app,  name="note")
app.add_typer(message_app, name="message")
app.add_typer(audio_app, name="audio")
app.add_typer(csv_app, name="csv")
app.add_typer(chat_app,  name="chat")

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
    accepted_col: str = typer.Option("", "--accepted-col", "-a", help="Column containing accept/reject status. Only rows with 'accept'/'accepted' are exported."),
    export_csv: Path = typer.Option(None, "--export-csv", help="Export a CSV of only the exported rows (all columns preserved)."),
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
        accepted_col=accepted_col or None,
        max_workers=workers,
        limit=limit,
        export_csv=export_csv,
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
    console.print(f"[bold green]Total: {len(results)} file(s)[/bold green]")

    # Write run log
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{csv_file.stem}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] source={csv_file.name} total={len(results)}\n")
        for path in results:
            lf.write(f"  {path.name}\n")
        lf.write("\n")
    console.print(f"[dim]Log saved → {log_file}[/dim]")

    if export_csv:
        console.print(f"[dim]Exported CSV → {export_csv}[/dim]")



@message_app.command("from-csv")
def message_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with message scripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write .txt files"),
    script_col: str = typer.Option("Script", "--script-col", help="Script column name"),
    participant_col: str = typer.Option("participant", "--participant-col", help="Participant column name"),
    data_type_col: str = typer.Option("Data_type", "--type-col", help="Data type column for filtering"),
    data_type_filter: str = typer.Option("", "--type", "-t", help="Filter by data type value. Empty = all rows."),
    accepted_col: str = typer.Option("", "--accepted-col", "-a", help="Column containing accept/reject status. Only rows with 'accept'/'accepted' are exported."),
    export_csv: Path = typer.Option(None, "--export-csv", help="Export a CSV of only the exported rows (all columns preserved)."),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process per run (0 = all)"),
):
    """Convert message Script rows in a CSV to individual .txt files."""
    from text_converter.message_to_txt import batch_from_csv

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    results = batch_from_csv(
        csv_path=csv_file,
        output_dir=output_dir,
        script_col=script_col,
        participant_col=participant_col,
        data_type_col=data_type_col,
        data_type_filter=data_type_filter or None,
        accepted_col=accepted_col or None,
        max_workers=workers,
        limit=limit,
        export_csv=export_csv,
    )

    if not results:
        console.print("[yellow]No rows found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Converted {len(results)} message(s) → {output_dir}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for i, path in enumerate(results, 1):
        table.add_row(str(i), path.name, f"{path.stat().st_size} B")
    console.print(table)
    console.print(f"[bold green]Total: {len(results)} file(s)[/bold green]")

    if export_csv:
        console.print(f"[dim]Exported CSV → {export_csv}[/dim]")


@audio_app.command("from-csv")
def audio_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with voicemail/audio transcripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write .txt files"),
    script_col: str = typer.Option("Script", "--script-col", help="Script column name"),
    participant_col: str = typer.Option("participant", "--participant-col", help="Participant column name"),
    data_type_col: str = typer.Option("Data_type", "--type-col", help="Data type column for filtering"),
    data_type_filter: str = typer.Option("", "--type", "-t", help="Filter by data type value. Empty = all rows."),
    accepted_col: str = typer.Option("", "--accepted-col", "-a", help="Column containing accept/reject status. Only rows with 'accept'/'accepted' are exported."),
    export_csv: Path = typer.Option(None, "--export-csv", help="Export a CSV of only the exported rows (all columns preserved)."),
    workers: int = typer.Option(1, "--workers", "-w", min=1, help="Number of parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process per run (0 = all)"),
):
    """Convert voicemail/audio transcript rows in a CSV to individual .txt files."""
    from text_converter.audio_to_text import batch_from_csv

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    results = batch_from_csv(
        csv_path=csv_file,
        output_dir=output_dir,
        script_col=script_col,
        participant_col=participant_col,
        data_type_col=data_type_col,
        data_type_filter=data_type_filter or None,
        accepted_col=accepted_col or None,
        max_workers=workers,
        limit=limit,
        export_csv=export_csv,
    )

    if not results:
        console.print("[yellow]No rows found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Converted {len(results)} transcript(s) → {output_dir}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for i, path in enumerate(results, 1):
        table.add_row(str(i), path.name, f"{path.stat().st_size} B")
    console.print(table)
    console.print(f"[bold green]Total: {len(results)} file(s)[/bold green]")

    if export_csv:
        console.print(f"[dim]Exported CSV → {export_csv}[/dim]")


@csv_app.command("subtract")
def csv_subtract(
    csv_file: Path = typer.Argument(..., help="Original CSV file to filter"),
    ref_file: Path = typer.Argument(..., help="File listing already-processed rows (CSV with id/index col, or .log/.txt with filenames)"),
    output: Path = typer.Argument(..., help="Output CSV path for remaining rows"),
    ref_col: str = typer.Option("", "--ref-col", help="Column in ref-file containing the processed IDs (e.g. 'index' or 'id'). Leave empty to parse filenames instead."),
    target_col: str = typer.Option("", "--target-col", help="Column in original CSV to match against (default: first column)."),
):
    """Remove already-processed rows from a CSV.

    Two modes depending on ref-file format:

    \b
    1. CSV ref-file with an ID column (contact.csv / events.csv style):
         tc csv subtract notes.csv contact.csv remaining.csv --ref-col index
         tc csv subtract notes.csv events.csv  remaining.csv --ref-col id

    \b
    2. Log/text file with filenames (0071_name.txt style):
         tc csv subtract notes.csv logs/run.log remaining.csv
    """
    from text_converter.csv_subtract import subtract

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)
    if not ref_file.exists():
        console.print(f"[red]File not found:[/red] {ref_file}")
        raise typer.Exit(1)

    kept, removed = subtract(
        csv_path=csv_file,
        ref_path=ref_file,
        output_path=output,
        ref_col=ref_col or None,
        target_col=target_col or None,
    )
    console.print(f"[green]✓[/green] Removed [bold]{removed}[/bold] row(s), kept [bold]{kept}[/bold] row(s)")
    console.print(f"[dim]Output → {output}[/dim]")


@chat_app.command("from-csv")
def chat_from_csv(
    csv_file: Path = typer.Argument(..., help="CSV file with chat scripts"),
    output_dir: Path = typer.Argument(..., help="Directory to write PNG screenshots"),
    script_col: str  = typer.Option("script",  "--script-col",  help="Script column name"),
    id_col: str      = typer.Option("id",       "--id-col",      help="ID column name"),
    qa_col: str      = typer.Option("QA",       "--qa-col",      help="QA status column name (used in output filename)"),
    accepted_col: str = typer.Option("", "--accepted-col", "-a",
                                     help="Column containing accept/reject status. Only 'accept'/'accepted' rows are exported."),
    export_csv: Path  = typer.Option(None, "--export-csv",
                                     help="Save a CSV of successfully processed rows (all columns + output_file path)."),
    done_csv: Path    = typer.Option(None, "--done-csv",
                                     help="Append processed rows (index, participant, filename) to this CSV."),
    participant_col: str = typer.Option("participant", "--participant-col", help="Participant column name (used for done-csv)"),
    filename_col: str = typer.Option("", "--filename-col", help="Column to use as output filename (instead of auto-generated {id}_{qa}.png)"),
    country_col: str = typer.Option("country", "--country-col", help="Country column for language localisation (EN/FR/IT/DE/ES)"),
    application_col: str = typer.Option("application used", "--application-col", help="Column for application name (iMessage/WhatsApp/Messenger/Telegram)"),
    os_col: str = typer.Option("OS", "--os-col", help="Column for OS info (iOS 17/Android 13/...)"),
    device_col: str = typer.Option("device info", "--device-col", help="Column for device name (iPhone 15 Pro Max/Samsung Galaxy S23/... )"),
    creation_col: str = typer.Option("Creation Date (YYYY.MM.DD)", "--creation-col", help="Column for creation date used as message date base (format: YYYY.MM.DD)"),
    templates_dir: Path = typer.Option(None, "--templates-dir",
                                       help="Custom templates directory (default: bundled package templates)"),
    workers: int  = typer.Option(8, "--workers", "-w", min=1, help="Parallel workers (default: 8)"),
    limit: int    = typer.Option(0, "--limit",   "-n", min=0,  help="Max rows to process (0 = all)"),
):
    """Generate mock chat screenshots (PNG) from a CSV of conversation scripts.

    Each row's script must follow the format:
        A: Xin chào
        B: Chào bạn
        C: Chào cả nhà   ← 3+ speakers = auto group chat

    Speaker A is always the sender (right side). Others are receivers (left side).
    Device, theme, and timestamp are randomised per row unless CSV has device columns.
    """
    from text_converter.chat_to_png import batch_from_csv

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    console.print(f"📂  [bold]{csv_file}[/bold]  →  {output_dir}")
    if accepted_col:
        console.print(f"[dim]Filter: {accepted_col} = accepted[/dim]")
    if limit:
        console.print(f"[dim]Limit: {limit} rows[/dim]")
    console.print()

    results = batch_from_csv(
        csv_path=csv_file,
        output_dir=output_dir,
        templates_dir=templates_dir,
        script_col=script_col,
        id_col=id_col,
        qa_col=qa_col,
        accepted_col=accepted_col or None,
        num_workers=workers,
        limit=limit,
        export_csv=export_csv,
        done_csv=done_csv,
        participant_col=participant_col,
        filename_col=filename_col or None,
        country_col=country_col,
        application_col=application_col,
        os_col=os_col,
        device_col=device_col,
        creation_col=creation_col,
    )

    if not results:
        console.print("[yellow]No rows processed.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Generated {len(results)} screenshot(s) → {output_dir}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for i, path in enumerate(results, 1):
        table.add_row(str(i), path.name, f"{path.stat().st_size // 1024} KB")
    console.print(table)
    console.print(f"[bold green]Total: {len(results)} file(s)[/bold green]")

    # Run log
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{csv_file.stem}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] source={csv_file.name} total={len(results)}\n")
        for path in results:
            lf.write(f"  {path.name}\n")
        lf.write("\n")
    console.print(f"[dim]Log saved → {log_file}[/dim]")

    if export_csv:
        console.print(f"[dim]Exported CSV → {export_csv}[/dim]")


def main():
    app()
