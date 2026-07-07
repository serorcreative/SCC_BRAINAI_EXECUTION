"""Index des exécutions (recherche déterministe)."""

from __future__ import annotations

from typing import Dict, List, Optional

from scc_brainai_execution.core.model import ExecutionRun


class ExecutionIndex:
    def __init__(self) -> None:
        self._by_id: Dict[str, ExecutionRun] = {}
        self._text: Dict[str, str] = {}

    def add(self, run: ExecutionRun) -> None:
        self._by_id[run.id] = run
        self._text[run.id] = f"{run.subject} {run.decision_id} {run.status}".lower()

    def rebuild(self, runs: List[ExecutionRun]) -> None:
        self._by_id.clear(); self._text.clear()
        for r in runs:
            self.add(r)

    def get(self, run_id: str) -> Optional[ExecutionRun]:
        return self._by_id.get(run_id)

    def search(self, *, status: Optional[str] = None, text: Optional[str] = None,
               limit: int = 50) -> List[ExecutionRun]:
        q = (text or "").strip().lower()
        out: List[ExecutionRun] = []
        for rid in sorted(self._by_id):
            r = self._by_id[rid]
            if status and r.status != status:
                continue
            if q and q not in self._text.get(rid, ""):
                continue
            out.append(r)
        return out[:limit] if limit and limit > 0 else out

    def all(self) -> List[ExecutionRun]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def __len__(self) -> int:
        return len(self._by_id)


__all__ = ["ExecutionIndex"]
