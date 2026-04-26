"""Bounded pool of 'simulation rooms' for consultant calls, with an
optional hard cap on total consultations as a cost ceiling.

Once `max_consultations` is reached the pool stops calling the LLM and
returns a `budget_exhausted=True` Verdict so the explorer tree can
finish gracefully and the trace records exactly where the cap was hit."""
import asyncio
from .agents.consultant import consult
from .types import AssignmentSpec, Verdict


class ConsultantPool:
    def __init__(
        self,
        spec: AssignmentSpec,
        n_rooms: int,
        max_consultations: int | None = None,
    ):
        self._spec = spec
        self._sem = asyncio.Semaphore(n_rooms)
        self._lock = asyncio.Lock()
        self.n_rooms = n_rooms
        self.max_consultations = max_consultations
        self.completed = 0
        self.refused = 0
        self._reserved = 0  # slots claimed but not yet completed

    async def request(self, history: list[str]) -> Verdict:
        async with self._lock:
            if self.max_consultations is not None and self._reserved >= self.max_consultations:
                self.refused += 1
                return Verdict(
                    quality=0.0, scope_fit=0.0,
                    notes="budget exhausted: consultant pool cap reached, leaf not evaluated",
                    n_consultations=0, budget_exhausted=True,
                )
            self._reserved += 1  # claim the slot atomically before releasing lock
        async with self._sem:
            verdict = await consult(self._spec, history)
            async with self._lock:
                self.completed += 1
            return verdict
