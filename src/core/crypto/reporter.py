"""Migration reporting engine for generating dashboards and audit artifacts."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class MigrationReporter:
    """Collects migration metrics and outputs rich console and persistent reports."""

    def __init__(self, command_name: str, mode: str) -> None:
        """Initialize migration reporter."""
        self.command_name = command_name
        self.mode = mode
        self.start_time = datetime.now(UTC)
        self.targets: list[dict[str, Any]] = []
        self.quarantined_items: list[dict[str, Any]] = []

    def record_target(
        self,
        target_name: str,
        total_count: int,
        migrated: int,
        skipped: int,
        quarantined: int = 0,
        conflicts: int = 0,
        errors: int = 0,
    ) -> None:
        """Record metrics for a specific model/target."""
        self.targets.append({
            "target": target_name,
            "total": total_count,
            "migrated": migrated,
            "skipped": skipped,
            "quarantined": quarantined,
            "conflicts": conflicts,
            "errors": errors,
        })

    def record_quarantine(
        self,
        model: str,
        pk: str,
        field: str,
        path: str,
        issue_type: str,
        error: str,
        action_taken: str = "SKIPPED_UNTOUCHED",
    ) -> None:
        """Record a quarantined or problematic item."""
        self.quarantined_items.append({
            "model": model,
            "pk": str(pk),
            "field": field,
            "path": path,
            "issue_type": issue_type,
            "error": error,
            "action_taken": action_taken,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    @property
    def total_scanned(self) -> int:
        """Total records or files scanned."""
        return sum(t["total"] for t in self.targets)

    @property
    def total_migrated(self) -> int:
        """Total records or files successfully migrated."""
        return sum(t["migrated"] for t in self.targets)

    @property
    def total_skipped(self) -> int:
        """Total records or files skipped."""
        return sum(t["skipped"] for t in self.targets)

    @property
    def total_quarantined(self) -> int:
        """Total records or files quarantined."""
        return sum(t["quarantined"] for t in self.targets)

    @property
    def total_conflicts(self) -> int:
        """Total records with concurrency conflicts."""
        return sum(t["conflicts"] for t in self.targets)

    @property
    def total_errors(self) -> int:
        """Total records with unhandled errors."""
        return sum(t["errors"] for t in self.targets)

    def write_reports(self, output_dir: Path | str | None = None) -> tuple[Path, Path]:
        """Write JSON manifest and Markdown summary to disk."""
        out_path = (
            Path("logs/migration_reports") if output_dir is None else Path(output_dir)
        )
        out_path.mkdir(parents=True, exist_ok=True)
        ts_str = self.start_time.strftime("%Y%m%d_%H%M%S")

        json_file = out_path / f"{self.command_name}_{ts_str}.json"
        md_file = out_path / f"{self.command_name}_{ts_str}.md"
        latest_json = out_path / f"{self.command_name}_latest.json"

        report_data = {
            "timestamp": self.start_time.isoformat(),
            "command": self.command_name,
            "mode": self.mode,
            "summary": {
                "total_scanned": self.total_scanned,
                "total_migrated": self.total_migrated,
                "total_skipped": self.total_skipped,
                "total_quarantined": self.total_quarantined,
                "total_conflicts": self.total_conflicts,
                "total_errors": self.total_errors,
            },
            "targets": self.targets,
            "quarantined_items": self.quarantined_items,
        }

        # 1. Write JSON
        json_file.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        shutil.copyfile(json_file, latest_json)

        # 2. Write Markdown
        md_lines = [
            f"# Migration Report: `{self.command_name}`\n",
            f"- **Mode**: `{self.mode}`",
            f"- **Executed At**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- **Total Scanned**: {self.total_scanned}",
            f"- **Total Migrated**: {self.total_migrated}",
            f"- **Total Skipped**: {self.total_skipped}",
            f"- **Total Quarantined**: {self.total_quarantined}",
            f"- **Total Conflicts**: {self.total_conflicts}",
            f"- **Total Errors**: {self.total_errors}\n",
            "## Target Breakdown\n",
            (
                "| Target Model & Field | Total | Migrated | Skipped | "
                "Quarantined | Conflicts | Errors |"
            ),
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        md_lines.extend(
            f"| `{t['target']}` | {t['total']} | {t['migrated']} | "
            f"{t['skipped']} | {t['quarantined']} | {t['conflicts']} | "
            f"{t['errors']} |"
            for t in self.targets
        )

        if self.quarantined_items:
            md_lines.append("\n## Quarantined Items\n")
            md_lines.append("| Model | PK | Field | Path | Issue Type | Error |")
            md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            md_lines.extend(
                f"| `{q['model']}` | `{q['pk']}` | `{q['field']}` | "
                f"`{q['path']}` | **{q['issue_type']}** | {q['error']} |"
                for q in self.quarantined_items
            )

        md_file.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

        return json_file, md_file

    def get_actionable_advice(self) -> list[str]:
        """Generate contextual next-step recommendations based on run outcomes."""
        advice: list[str] = []

        if self.mode == "dry_run":
            advice.append(
                f"[bold green]DRY-RUN COMPLETE[/bold green]: "
                f"Validated {self.total_scanned} records. "
                "0 modifications made to database or disk.\n"
                "To execute live: uv run python manage.py "
                f"{self.command_name} --execute"
            )

        if self.total_quarantined > 0:
            advice.append(
                "[bold yellow]QUARANTINED ITEMS "
                f"({self.total_quarantined})[/bold yellow]: "
                "Files or records had missing files or unreadable permissions.\n"
                "Review the quarantine report above to inspect individual record IDs."
            )

        if self.total_conflicts > 0:
            advice.append(
                "[bold yellow]CONCURRENCY CONFLICTS "
                f"({self.total_conflicts})[/bold yellow]: "
                "Records were modified by active users during migration.\n"
                "User changes were preserved. Re-run: "
                f"uv run python manage.py {self.command_name} --execute"
            )

        if self.total_errors > 0:
            advice.append(
                f"[bold red]ERRORS ENCOUNTERED ({self.total_errors})[/bold red]: "
                "Check error logs and resolve underlying issues before re-running."
            )

        return advice

    def print_summary(self, console: Console | None = None) -> None:
        """Render terminal table and actionable next steps box."""
        if console is None:
            console = Console()

        table = Table(title=f"Migration Summary: {self.command_name} ({self.mode})")
        table.add_column("Target Model & Field", style="bold cyan")
        table.add_column("Total", justify="right")
        table.add_column("Migrated", justify="right", style="bold green")
        table.add_column("Skipped", justify="right", style="yellow")
        table.add_column("Quarantined", justify="right", style="bold magenta")
        table.add_column("Conflicts", justify="right", style="bold yellow")
        table.add_column("Errors", justify="right", style="bold red")

        for t in self.targets:
            table.add_row(
                t["target"],
                str(t["total"]),
                str(t["migrated"]),
                str(t["skipped"]),
                str(t["quarantined"]),
                str(t["conflicts"]),
                str(t["errors"]),
            )

        console.print(table)

        advice_lines = self.get_actionable_advice()
        if advice_lines:
            panel_content = "\n\n".join(advice_lines)
            console.print(
                Panel(panel_content, title="Actionable Next Steps", expand=False)
            )
