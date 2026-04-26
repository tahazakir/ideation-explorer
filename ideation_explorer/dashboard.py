"""Rich live dashboard for the ideation explorer.

Shows the decision tree growing in real time, a consultant pool progress bar,
and a status line.

Usage:
    python -m ideation_explorer.dashboard \
        --assignment ml_notebook --rooms 3 --depth 2 --options 2 \
        [--max-consultations N] [--min-margin F] [--out PATH] [--plan-out PATH]
"""
import argparse
import asyncio
import importlib
import json
import os
import time
import threading
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .consultant_pool import ConsultantPool
from .explorer import explore
from .main import assess_confidence, build_run_record, load_assignment
from .recorder import RECORDER
from .types import AssignmentSpec, NodeResult

console = Console()


class DashboardState:
    """Mutable state updated by on_event, read by the Rich refresh loop."""

    def __init__(self, max_leaves: int):
        self._lock = threading.Lock()
        self.max_leaves = max_leaves
        self.leaves_done = 0
        self.leaves_queued = 0
        self.last_status = "starting..."
        self.elapsed = 0.0
        # rich Tree for the decision tree panel
        self.rich_tree = Tree("[bold cyan]Decision Tree[/bold cyan]")
        # map history-tuple -> rich Tree node (for updating labels)
        self._nodes: dict[tuple, object] = {(): self.rich_tree}

    def on_event(self, evt: dict) -> None:
        t = evt["type"]
        with self._lock:
            if t == "split":
                history = tuple(evt["history"])
                decision = evt["decision"]
                options = evt["options"]
                parent_key = history  # this node is the parent
                parent_node = self._nodes.get(parent_key, self.rich_tree)
                label = f"[cyan][split][/cyan] [bold]{decision[:50]}[/bold]"
                branch_node = parent_node.add(label)
                # pre-add option placeholders as children
                for opt in options:
                    child_key = history + (opt,)
                    child_node = branch_node.add(f"[dim]{opt[:40]}[/dim]")
                    self._nodes[child_key] = child_node
                self.last_status = f"[split] depth={evt['depth']} — {decision[:60]}"

            elif t == "leaf":
                history = tuple(evt["history"])
                node = self._nodes.get(history)
                if node is not None:
                    node.label = Text.from_markup(
                        f"[yellow]⏳ consulting...[/yellow] {' → '.join(history[-2:])}"
                    )
                self.leaves_queued += 1
                self.last_status = f"[leaf] queued consultant for: {' → '.join(history[-2:])}"

            elif t == "leaf_done":
                history = tuple(evt["history"])
                v = evt["verdict"]
                node = self._nodes.get(history)
                if node is not None:
                    if v.budget_exhausted:
                        node.label = Text.from_markup(
                            f"[red]✗ budget hit[/red] {' → '.join(history[-2:])}"
                        )
                    else:
                        node.label = Text.from_markup(
                            f"[green]✓[/green] q={v.quality:.2f} scope={v.scope_fit:.2f} "
                            f"[dim]{v.notes[:60]}[/dim]"
                        )
                self.leaves_done += 1
                self.last_status = (
                    f"[leaf done] q={v.quality:.2f} scope={v.scope_fit:.2f} | "
                    f"{' → '.join(history[-2:])}"
                )

            elif t == "merge":
                history = tuple(evt["history"])
                decision = evt["decision"]
                best = evt["best"]
                avg_q = evt["avg_q"]
                node = self._nodes.get(history)
                if node is not None:
                    node.label = Text.from_markup(
                        f"[cyan][merge][/cyan] [bold]{decision[:40]}[/bold] "
                        f"best=[green]{best[:30]}[/green] avg_q={avg_q:.2f}"
                    )
                self.last_status = f"[merge] {decision[:50]} best={best[:30]}"

    def make_layout(self) -> Layout:
        with self._lock:
            # tree panel
            tree_panel = Panel(self.rich_tree, title="[bold]Ideation Tree[/bold]", border_style="cyan")

            # pool progress panel
            done = self.leaves_done
            total = max(self.max_leaves, 1)
            bar_width = 40
            filled = int(bar_width * done / total)
            bar = "[green]" + "█" * filled + "[/green][dim]" + "░" * (bar_width - filled) + "[/dim]"
            pool_text = Text.from_markup(
                f"Consultant pool  {bar}  {done}/{total} leaves done\n"
                f"Queued: {self.leaves_queued}   Elapsed: {self.elapsed:.1f}s"
            )
            pool_panel = Panel(pool_text, title="[bold]Pool Progress[/bold]", border_style="yellow")

            # status panel
            status_panel = Panel(
                Text.from_markup(self.last_status),
                title="[bold]Status[/bold]",
                border_style="dim",
            )

        layout = Layout()
        layout.split_column(
            Layout(tree_panel, name="tree", ratio=7),
            Layout(pool_panel, name="pool", ratio=2),
            Layout(status_panel, name="status", ratio=1),
        )
        return layout


async def run_with_dashboard(
    assignment: str,
    rooms: int,
    depth: int,
    options: int,
    max_consultations: int | None = None,
    min_margin: float = 0.05,
    out: str | None = None,
    plan_out: str | None = None,
) -> None:
    spec = load_assignment(assignment)
    pool = ConsultantPool(spec, n_rooms=rooms, max_consultations=max_consultations)
    RECORDER.reset()

    max_leaves = options ** depth
    state = DashboardState(max_leaves=max_leaves)
    t0 = time.time()

    console.print(f"\n[bold cyan]=== Ideation Explorer: {spec.title} ===[/bold cyan]\n")

    with Live(state.make_layout(), console=console, refresh_per_second=4, screen=False) as live:
        def on_event(evt: dict) -> None:
            state.elapsed = time.time() - t0
            state.on_event(evt)
            live.update(state.make_layout())

        root = await explore(
            spec, pool, history=[],
            max_depth=depth, max_options=options,
            on_event=on_event,
        )

    # result panel (printed after Live exits so it's fully visible for screencapture)
    from .main import assess_confidence, build_run_record

    class _FakeArgs:
        pass

    fake_args = _FakeArgs()
    fake_args.assignment = assignment
    fake_args.rooms = rooms
    fake_args.depth = depth
    fake_args.options = options
    fake_args.max_consultations = max_consultations
    fake_args.min_margin = min_margin
    fake_args.out = out
    fake_args.plan_out = plan_out

    advisory = assess_confidence(root, min_margin)
    record = build_run_record(spec, root, fake_args, advisory, pool)

    console.print("\n[bold]=== Result ===[/bold]")
    console.print(
        f"Consultations: completed={pool.completed} refused={pool.refused}"
        + (f"  (cap={max_consultations})" if max_consultations else "")
    )
    m = record["metrics"]
    console.print(f"Wall time:     {m['wall_time_s']:.2f}s")
    console.print(f"LLM calls:     {m['total_calls']}  "
                  f"(in_tok={m['total_input_tokens']}, out_tok={m['total_output_tokens']})")
    console.print(f"Root quality:  {root.verdict.quality:.3f}  "
                  f"(stddev={root.verdict.quality_stddev:.3f})")

    if root.branches:
        console.print("\n[bold]Per-option breakdown at root:[/bold]")
        for b in sorted(root.branches, key=lambda x: -x.verdict.quality):
            tag = "  [red][BUDGET-HIT][/red]" if b.verdict.budget_exhausted else ""
            console.print(f"  [cyan]-[/cyan] {b.option}{tag}")
            console.print(f"      quality={b.verdict.quality:.3f}  "
                          f"scope_fit={b.verdict.scope_fit:.2f}  n={b.verdict.n_consultations}")
            console.print(f"      notes: [dim]{b.verdict.notes[:160]}[/dim]")

    console.print()
    if advisory["refused"]:
        console.print(f"[bold red]!! LOW CONFIDENCE -- recommendation withheld.[/bold red]")
        console.print(f"   reason: {advisory['reason']}")
    else:
        console.print("[bold green]RECOMMENDED FULL PLAN:[/bold green]")
        for i, step in enumerate(root.best_path(), 1):
            console.print(f"  {i}. {step}")

    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w") as f:
            json.dump(record, f, indent=2)
        console.print(f"\nTrace written to {out}")

    if plan_out and not advisory["refused"]:
        os.makedirs(os.path.dirname(plan_out) or ".", exist_ok=True)
        plan = {
            "assignment": record["assignment"],
            "recommended_plan": record["recommended_plan"],
            "expected_quality": root.verdict.quality,
            "expected_days": root.verdict.scope_fit,
            "advisory": advisory,
        }
        with open(plan_out, "w") as f:
            json.dump(plan, f, indent=2)
        console.print(f"Plan written to {plan_out}")
    elif plan_out and advisory["refused"]:
        console.print(f"[yellow]Plan NOT written to {plan_out} (low confidence).[/yellow]")


def parse_args():
    p = argparse.ArgumentParser(description="Ideation explorer with Rich live dashboard.")
    p.add_argument("--assignment", default="dummy")
    p.add_argument("--rooms", type=int, default=2)
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--options", type=int, default=3)
    p.add_argument("--max-consultations", type=int, default=None)
    p.add_argument("--min-margin", type=float, default=0.05)
    p.add_argument("--out", default=None)
    p.add_argument("--plan-out", default=None)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_with_dashboard(
        assignment=args.assignment,
        rooms=args.rooms,
        depth=args.depth,
        options=args.options,
        max_consultations=args.max_consultations,
        min_margin=args.min_margin,
        out=args.out,
        plan_out=args.plan_out,
    ))
