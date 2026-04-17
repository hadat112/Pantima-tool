"""CLI entry point for note conversion tools."""

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="tc", help="Note conversion tools.", no_args_is_help=True)
note_app = typer.Typer(help="Convert notes to text or PNG.", no_args_is_help=True)
app.add_typer(note_app, name="note")

console = Console()


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

    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{csv_file.stem}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] source={csv_file.name} total={len(results)}\\n")
        for path in results:
            lf.write(f"  {path.name}\\n")
        lf.write("\\n")
    console.print(f"[dim]Log saved → {log_file}[/dim]")

    if export_csv:
        console.print(f"[dim]Exported CSV → {export_csv}[/dim]")


@note_app.command("to-png")
def note_to_png(
    csv_file: Path = typer.Argument(..., help="CSV file with note content"),
    output_dir: Path = typer.Argument(..., help="Directory to write PNG screenshots"),
    template_col: str = typer.Option("Template", "--template-col", help="Column containing note content"),
    device_col: str = typer.Option("Device", "--device-col", help="Column containing device name"),
    os_col: str = typer.Option("OS", "--os-col", help="Column containing OS version or resolution"),
    spec_col: str = typer.Option("spec", "--spec-col", help="Column containing screen resolution (e.g. 1170x2532)"),
    filename_col: str = typer.Option("", "--filename-col", help="Column to use as output filename (optional)"),
    templates_dir: Path = typer.Option(None, "--templates-dir", help="Custom templates directory"),
    export_csv: Path = typer.Option(None, "--export-csv", help="Export a CSV of successfully processed rows"),
    done_csv: Path = typer.Option(None, "--done-csv", help="Append processed rows (index, filename) to this CSV"),
    workers: int = typer.Option(8, "--workers", "-w", min=1, help="Parallel workers"),
    limit: int = typer.Option(0, "--limit", "-n", min=0, help="Max rows to process (0 = all)"),
):
    """Generate note app screenshots (PNG) from CSV rows."""
    from text_converter.note_to_png import batch_from_csv

    if not csv_file.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    console.print(f"📂  [bold]{csv_file}[/bold]  →  {output_dir}")
    if limit:
        console.print(f"[dim]Limit: {limit} rows[/dim]")
    console.print()

    results = batch_from_csv(
        csv_path=csv_file,
        output_dir=output_dir,
        templates_dir=templates_dir,
        template_col=template_col,
        device_col=device_col,
        os_col=os_col,
        spec_col=spec_col,
        filename_col=filename_col or None,
        num_workers=workers,
        limit=limit,
        export_csv=export_csv,
        done_csv=done_csv,
    )

    if not results:
        console.print("[yellow]No rows processed.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Generated {len(results)} note screenshot(s) → {output_dir}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    for i, path in enumerate(results, 1):
        table.add_row(str(i), path.name, f"{path.stat().st_size // 1024} KB")
    console.print(table)
    console.print(f"[bold green]Total: {len(results)} file(s)[/bold green]")

    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{csv_file.stem}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] source={csv_file.name} total={len(results)}\\n")
        for path in results:
            lf.write(f"  {path.name}\\n")
        lf.write("\\n")
    console.print(f"[dim]Log saved → {log_file}[/dim]")

    if export_csv:
        console.print(f"[dim]Exported CSV → {export_csv}[/dim]")


def main() -> None:
    app()
