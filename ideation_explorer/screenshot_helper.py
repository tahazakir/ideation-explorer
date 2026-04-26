"""Automate all 9 screenshots required for Phase 3 submission.

Live screenshots (02-05, 08) open a Terminal window running the Rich dashboard,
wait for the right moment, and capture real terminal pixels with macOS screencapture.

Static screenshots (01, 06, 07, 09) use Pillow / graphviz (no LLM calls).

Usage:
    python -m ideation_explorer.screenshot_helper              # all 9
    python -m ideation_explorer.screenshot_helper --skip-live-runs  # static only
    python -m ideation_explorer.screenshot_helper --only 01 06 07 09
    python -m ideation_explorer.screenshot_helper --only 05    # F3 trace only
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import graphviz

# ── paths ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
RUNS_DIR = PROJECT_ROOT / "outputs" / "runs"
EVAL_DIR = PROJECT_ROOT / "eval"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# ── A: static-render helpers (Pillow) ─────────────────────────────────────────

def run_command(cmd: list[str], timeout: int = 360) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=timeout,
    )
    out = result.stdout
    if result.stderr:
        out += "\n--- stderr ---\n" + result.stderr
    return out


def _load_font(size: int = 13):
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Courier New.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


_BG       = (30, 30, 30)
_DEFAULT  = (204, 204, 204)
_CYAN     = (86, 182, 194)
_AMBER    = (229, 192, 123)
_GREEN    = (152, 195, 121)
_RED      = (224, 108, 117)
_BRIGHT   = (240, 240, 240)
_KEY_BLUE = (97, 175, 239)


def _line_color(line: str, syntax_mode: str | None) -> tuple[int, int, int]:
    if syntax_mode == "json":
        stripped = line.strip()
        if re.match(r'"[^"]+"\s*:', stripped):
            return _KEY_BLUE
        if re.match(r':\s*"', stripped) or re.search(r':\s*"[^"]*"', stripped):
            return _AMBER
        if re.search(r':\s*(true|false|null|\d)', stripped):
            return _GREEN
        return _DEFAULT

    if any(tag in line for tag in ("[split]", "[merge]", "[leaf]")):
        return _CYAN
    if "LOW CONFIDENCE" in line or "!!" in line:
        return _AMBER
    if "RECOMMENDED FULL PLAN" in line:
        return _GREEN
    if "refused=" in line or "BUDGET" in line or "budget_exhausted" in line:
        return _RED
    if line.startswith("  -") or line.startswith("    -"):
        return _BRIGHT
    return _DEFAULT


def render_terminal_png(
    text: str,
    out_path: Path,
    title: str = "",
    syntax_mode: str | None = None,
) -> None:
    font = _load_font(13)
    pad = 20
    line_height = 18

    lines = text.splitlines()
    if title:
        lines = [f"# {title}", ""] + lines

    try:
        bbox = font.getbbox("M")
        char_w = bbox[2] - bbox[0]
    except AttributeError:
        char_w = 8

    max_chars = max((len(l) for l in lines), default=80)
    width = max(900, max_chars * char_w + 2 * pad)
    height = len(lines) * line_height + 2 * pad

    img = Image.new("RGB", (width, height), _BG)
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        color = _line_color(line, syntax_mode)
        y = pad + i * line_height
        draw.text((pad, y), line, font=font, fill=color)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path))
    print(f"  -> {out_path.name}")


# ── B: live capture via AppleScript + screencapture ──────────────────────────

def _build_dashboard_cmd(
    assignment: str,
    rooms: int,
    depth: int,
    options: int,
    extra_flags: str = "",
    out: str = "",
    plan_out: str = "",
) -> str:
    """Build the shell command string to paste into Terminal."""
    parts = [
        sys.executable, "-m", "ideation_explorer.dashboard",
        "--assignment", assignment,
        "--rooms", str(rooms),
        "--depth", str(depth),
        "--options", str(options),
    ]
    if extra_flags:
        parts += extra_flags.split()
    if out:
        parts += ["--out", out]
    if plan_out:
        parts += ["--plan-out", plan_out]
    # cd first so relative paths work
    cmd_str = f"cd {PROJECT_ROOT} && {' '.join(parts)}"
    return cmd_str


def _open_terminal_with_cmd(cmd_str: str, window_size: tuple = (1300, 850)) -> None:
    """Open a new Terminal window running cmd_str, sized for screencapture."""
    w, h = window_size
    script = f'''
tell application "Terminal"
    activate
    do script "{cmd_str.replace('"', '\\"')}"
    delay 0.5
    set bounds of front window to {{50, 50, {50 + w}, {50 + h}}}
end tell
'''
    subprocess.run(["osascript", "-e", script], check=True)


def _screencapture(out_path: Path, delay_s: int = 2) -> None:
    """Capture the frontmost window after delay_s seconds."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["screencapture", "-T", str(delay_s), "-o", "-l",
         _get_front_window_id(), str(out_path)],
        check=False,  # fallback silently if window-id fails
    )
    # If window-id approach failed, grab full screen fallback
    if not out_path.exists():
        subprocess.run(
            ["screencapture", f"-T{delay_s}", str(out_path)],
            check=True,
        )
    print(f"  -> {out_path.name} (screencapture)")


def _get_front_window_id() -> str:
    """Return the CGWindowID of the frontmost Terminal window (best-effort)."""
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "Terminal" to get id of front window'],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return "0"


def _close_terminal_window() -> None:
    subprocess.run(
        ["osascript", "-e",
         'tell application "Terminal" to close front window'],
        check=False,
    )


def _wait_for_file(path: Path, timeout: int = 180, poll: float = 2.0) -> bool:
    """Poll until path exists or timeout elapses. Returns True if found."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            return True
        time.sleep(poll)
    return False


# ── C: individual capture functions ──────────────────────────────────────────

def capture_01_help() -> None:
    out = run_command([sys.executable, "-m", "ideation_explorer.main", "--help"])
    render_terminal_png(out, SCREENSHOTS_DIR / "01_landing_help.png",
                        title="Entry point & governance flags")


def capture_02_and_03() -> None:
    """Launch ml_notebook dashboard; mid-run screenshot for 02, post-run for 03."""
    trace_path = RUNS_DIR / "ml_notebook.json"
    # remove stale trace so we can poll for fresh one
    if trace_path.exists():
        trace_path.unlink()

    cmd = _build_dashboard_cmd(
        "ml_notebook", rooms=3, depth=2, options=2,
        out="outputs/runs/ml_notebook.json",
        plan_out="outputs/recommended_plans/ml_notebook.json",
    )
    print("  opening Terminal for ml_notebook dashboard run...")
    _open_terminal_with_cmd(cmd)

    # screenshot 02: tree mid-build (~15s into ~30s run)
    print("  waiting 18s for tree to be partially built...")
    time.sleep(18)
    _screencapture(SCREENSHOTS_DIR / "02_main_run_tree.png", delay_s=1)

    # wait for run to finish (trace file written)
    print("  waiting for run to finish...")
    found = _wait_for_file(trace_path, timeout=120)
    if not found:
        print("  [warn] trace not found after timeout; screencapturing anyway")
    time.sleep(4)  # let result panel render fully
    _screencapture(SCREENSHOTS_DIR / "03_result_panel.png", delay_s=1)

    _close_terminal_window()


def capture_04_low_confidence() -> None:
    cmd = _build_dashboard_cmd(
        "dummy", rooms=2, depth=1, options=2,
        extra_flags="--min-margin 0.99",
    )
    print("  opening Terminal for low-confidence governance gate...")
    _open_terminal_with_cmd(cmd)
    print("  waiting 25s for run to finish...")
    time.sleep(25)
    _screencapture(SCREENSHOTS_DIR / "04_low_confidence_refusal.png", delay_s=1)
    _close_terminal_window()


def capture_05_budget_exhausted() -> None:
    trace_path = RUNS_DIR / "vague_budget_capped.json"
    if trace_path.exists():
        trace_path.unlink()

    cmd = _build_dashboard_cmd(
        "vague", rooms=3, depth=3, options=3,
        extra_flags="--max-consultations 5 --min-margin 0.05",
        out="outputs/runs/vague_budget_capped.json",
        plan_out="outputs/recommended_plans/vague_budget_capped.json",
    )
    print("  opening Terminal for F3 budget-cap run...")
    _open_terminal_with_cmd(cmd)
    print("  waiting for budget cap to be hit...")
    found = _wait_for_file(trace_path, timeout=180)
    if not found:
        print("  [warn] trace not found after timeout; screencapturing anyway")
    time.sleep(4)
    _screencapture(SCREENSHOTS_DIR / "05_budget_exhausted.png", delay_s=1)
    _close_terminal_window()


def capture_06_eval_csv() -> None:
    csv_path = EVAL_DIR / "evaluation_results.csv"
    text = csv_path.read_text()
    rows = [line.split(",") for line in text.splitlines()]
    col_widths = [max(len(r[i]) if i < len(r) else 0 for r in rows) for i in range(max(len(r) for r in rows))]
    lines = []
    for row in rows:
        lines.append("  ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))
    render_terminal_png("\n".join(lines), SCREENSHOTS_DIR / "06_evaluation_csv.png",
                        title="eval/evaluation_results.csv")


def capture_07_trace_json() -> None:
    trace_path = RUNS_DIR / "ml_notebook.json"
    text = "\n".join(trace_path.read_text().splitlines()[:60])
    render_terminal_png(text, SCREENSHOTS_DIR / "07_trace_json.png",
                        title="outputs/runs/ml_notebook.json — LLM call trace",
                        syntax_mode="json")


def capture_08_executor_tasks() -> None:
    plan_path = OUTPUTS_DIR / "recommended_plans" / "ml_notebook.json"
    if not plan_path.exists():
        print("  [warn] ml_notebook plan not found; run 02/03 first")
        return
    cmd_str = (
        f"cd {PROJECT_ROOT} && {sys.executable} -m ideation_explorer.executor "
        f"outputs/recommended_plans/ml_notebook.json "
        f"--out outputs/exec_plans/ml_notebook_tasks.json"
    )
    _open_terminal_with_cmd(cmd_str)
    print("  waiting 25s for executor...")
    time.sleep(25)
    _screencapture(SCREENSHOTS_DIR / "08_executor_tasks.png", delay_s=1)
    _close_terminal_window()


def capture_09_architecture() -> None:
    trace_path = RUNS_DIR / "ml_notebook.json"
    out_path = SCREENSHOTS_DIR / "09_architecture"
    build_decision_tree_graphviz(trace_path, out_path)


# ── D: graphviz tree builder ──────────────────────────────────────────────────

def build_decision_tree_graphviz(trace_path: Path, out_path: Path) -> None:
    data = json.loads(trace_path.read_text())
    title = data["assignment"]["title"][:50]
    root_q = data["root"]["verdict"]["quality"]

    dot = graphviz.Digraph(
        name="IdeationDecisionTree",
        format="png",
        graph_attr={
            "rankdir": "TB",
            "bgcolor": "#1e1e1e",
            "fontcolor": "white",
            "splines": "ortho",
            "nodesep": "0.5",
            "ranksep": "0.8",
            "label": f"Decision Tree: {title}\nroot q={root_q:.3f}",
            "labelloc": "t",
            "fontname": "Courier",
            "fontsize": "14",
        },
        node_attr={"style": "filled", "fontcolor": "white", "fontname": "Courier", "fontsize": "10"},
        edge_attr={"fontcolor": "#cccccc", "fontname": "Courier", "fontsize": "9"},
    )

    counter = [0]

    def add_node(node_dict: dict, parent_id: str | None = None,
                 edge_label: str = "", is_best: bool = False) -> str:
        my_id = str(counter[0]); counter[0] += 1
        v = node_dict["verdict"]
        quality = v["quality"]
        stddev = v.get("quality_stddev", 0.0)
        n = v.get("n_consultations", 1)
        budget_hit = v.get("budget_exhausted", False)

        if node_dict.get("is_leaf"):
            label_top = "LEAF"
            shape = "ellipse"
        elif parent_id is None:
            label_top = (node_dict.get("decision") or "ROOT")[:30]
            shape = "doubleoctagon"
        else:
            label_top = (node_dict.get("decision") or "?")[:30]
            shape = "box"

        label = f"{label_top}\nq={quality:.2f}  σ={stddev:.2f}\nn={n}"
        if budget_hit:
            label += "\n[BUDGET HIT]"

        if budget_hit:
            fillcolor = "#9E9E9E"
        elif quality >= 0.75:
            fillcolor = "#4CAF50"
        elif quality >= 0.65:
            fillcolor = "#FF9800"
        else:
            fillcolor = "#F44336"

        penwidth = "3.0" if is_best else "1.0"
        style = "rounded,filled" if shape == "box" else "filled"

        dot.node(my_id, label=label, shape=shape, fillcolor=fillcolor,
                 penwidth=penwidth, style=style)

        if parent_id is not None:
            edge_color = "#4CAF50" if is_best else "#999999"
            edge_style = "solid" if is_best else "dashed"
            dot.edge(parent_id, my_id, label=edge_label[:25],
                     color=edge_color, style=edge_style,
                     penwidth="2.0" if is_best else "1.0")

        chosen = node_dict.get("chosen_best_option")
        for branch in node_dict.get("branches", []):
            add_node(branch["child"], my_id,
                     edge_label=branch["option"],
                     is_best=(branch["option"] == chosen))

        return my_id

    add_node(data["root"])
    dot.render(str(out_path), cleanup=True)
    print(f"  -> {out_path.name}.png")


# ── E: orchestrator ───────────────────────────────────────────────────────────

LIVE_RUN_TASKS = {"02", "03", "04", "05", "08"}

ALL_TASKS: dict[str, tuple[str, callable]] = {
    "01": ("01_landing_help.png",           capture_01_help),
    "02": ("02_main_run_tree.png",          None),   # handled by capture_02_and_03
    "03": ("03_result_panel.png",           None),   # handled by capture_02_and_03
    "04": ("04_low_confidence_refusal.png", capture_04_low_confidence),
    "05": ("05_budget_exhausted.png",       capture_05_budget_exhausted),
    "06": ("06_evaluation_csv.png",         capture_06_eval_csv),
    "07": ("07_trace_json.png",             capture_07_trace_json),
    "08": ("08_executor_tasks.png",         capture_08_executor_tasks),
    "09": ("09_architecture.png",           capture_09_architecture),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture all submission screenshots.")
    parser.add_argument("--only", nargs="*", metavar="N",
                        help="run only these screenshot numbers e.g. --only 01 05 09")
    parser.add_argument("--skip-live-runs", action="store_true",
                        help="skip screenshots that require live LLM calls (02 03 04 05 08)")
    args = parser.parse_args()

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    selected = set(args.only if args.only else list(ALL_TASKS.keys()))
    ordered = sorted(selected, key=lambda k: int(k))

    # 02 and 03 are captured together in one Terminal session
    need_02_03 = ("02" in selected or "03" in selected) and not args.skip_live_runs
    did_02_03 = False

    for key in ordered:
        if key not in ALL_TASKS:
            print(f"[unknown] {key} — skipping")
            continue
        if args.skip_live_runs and key in LIVE_RUN_TASKS:
            print(f"[skip] {key} (live run)")
            continue
        if key in ("02", "03"):
            if not did_02_03 and need_02_03:
                print("[02+03] capturing run-tree + result panel (single Terminal session)...")
                try:
                    capture_02_and_03()
                    print("[02+03] done")
                except Exception as e:
                    print(f"[02+03] ERROR: {e}")
                did_02_03 = True
            continue

        filename, fn = ALL_TASKS[key]
        print(f"[{key}] capturing {filename}...")
        try:
            fn()
            print(f"[{key}] done")
        except Exception as e:
            print(f"[{key}] ERROR: {e}")

    print(f"\nScreenshots written to {SCREENSHOTS_DIR}")


if __name__ == "__main__":
    main()
