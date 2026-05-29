"""Rich-based structured logging with progress bars."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()


def phase_start(phase: str, title: str) -> None:
    """Log the start of a pipeline phase."""
    console.print(f"\n[bold cyan][{phase}][/bold cyan] {title}...")


def phase_done(phase: str, summary: str) -> None:
    """Log the completion of a pipeline phase."""
    console.print(f"  [green]✓[/green] {summary}")


def phase_skip(phase: str, reason: str) -> None:
    """Log a skipped phase."""
    console.print(f"  [yellow]⊘[/yellow] Skipped: {reason}")


def phase_error(phase: str, error: str) -> None:
    """Log a phase error."""
    console.print(f"  [red]✗[/red] Error: {error}")


def info(msg: str) -> None:
    console.print(f"  [dim]{msg}[/dim]")


def warn(msg: str) -> None:
    console.print(f"  [yellow]⚠[/yellow] {msg}")


def error(msg: str) -> None:
    console.print(f"  [red]✗[/red] {msg}")


def success(msg: str) -> None:
    console.print(f"  [green]✓[/green] {msg}")


def banner(title: str, subtitle: str = "") -> None:
    """Display the Forge Core banner."""
    text = f"[bold blue]{title}[/bold blue]"
    if subtitle:
        text += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(text, border_style="blue", padding=(1, 4)))


def coverage_table(before: float, after: float, tests_before: int, tests_after: int) -> None:
    """Display a before/after coverage comparison table."""
    table = Table(title="Coverage Results", border_style="blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Before", style="red")
    table.add_column("After", style="green")
    table.add_column("Delta", style="yellow")

    table.add_row(
        "Line Coverage",
        f"{before:.1f}%",
        f"{after:.1f}%",
        f"+{after - before:.1f}%",
    )
    table.add_row(
        "Total Tests",
        str(tests_before),
        str(tests_after),
        f"+{tests_after - tests_before}",
    )
    console.print(table)


def create_progress() -> Progress:
    """Create a Rich progress bar for phase tracking."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
