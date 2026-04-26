"""Recursive explorer agent. Each call is one node in the decision tree."""
import asyncio
from .agents.option_generator import generate_options
from .aggregate import aggregate
from .consultant_pool import ConsultantPool
from .types import AssignmentSpec, BranchReport, NodeResult


async def explore(
    spec: AssignmentSpec,
    pool: ConsultantPool,
    history: list[str],
    max_depth: int = 3,
    max_options: int = 3,
    indent: int = 0,
    on_event=None,
) -> NodeResult:
    pad = "  " * indent
    decision, options = await generate_options(spec, history, max_options, max_depth)

    def _emit(evt: dict) -> None:
        if on_event:
            on_event(evt)
        else:
            # default plain-print fallback
            t = evt["type"]
            if t == "split":
                print(f"{pad}[split] depth={evt['depth']} decision='{evt['decision']}' options={evt['options']}")
            elif t == "leaf":
                print(f"{pad}[leaf] history={evt['history']} -> queueing consultant")
            elif t == "leaf_done":
                v = evt["verdict"]
                print(f"{pad}[leaf done] q={v.quality:.2f} scope={v.scope_fit:.2f} :: {v.notes[:80]}")
            elif t == "merge":
                print(f"{pad}[merge] decision='{evt['decision']}' best='{evt['best']}' avg_q={evt['avg_q']:.2f}")

    if not options:
        _emit({"type": "leaf", "history": history})
        verdict = await pool.request(history)
        _emit({"type": "leaf_done", "history": history, "verdict": verdict})
        return NodeResult(history=history, verdict=verdict, is_leaf=True)

    _emit({"type": "split", "depth": len(history), "decision": decision, "options": options, "history": history})

    async def run_child(opt: str) -> BranchReport:
        child = await explore(spec, pool, history + [opt], max_depth, max_options, indent + 1, on_event)
        return BranchReport(option=opt, verdict=child.verdict, child=child)

    branches = await asyncio.gather(*(run_child(opt) for opt in options))
    rolled, best = aggregate(branches)
    _emit({"type": "merge", "decision": decision, "best": best, "avg_q": rolled.quality, "history": history})
    return NodeResult(
        history=history,
        verdict=rolled,
        decision=decision,
        branches=branches,
        chosen_best_option=best,
    )
