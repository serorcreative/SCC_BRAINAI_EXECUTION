"""Journal d'événements d'exécution + traces exploitables par Memory plus tard.

Append-only, déterministe (horodatage figé ``as_of``). Les **traces** sont produites
dans un format neutre qu'une future intégration Memory pourra ingérer — Execution
n'écrit **jamais** dans Memory.
"""

from __future__ import annotations

from typing import Any, Dict, List


class EventLog:
    def __init__(self, as_of: str):
        self._as_of = as_of
        self._events: List[Dict[str, Any]] = []

    def emit(self, type: str, subject: str = "", payload: Dict[str, Any] = None) -> Dict[str, Any]:
        evt = {"seq": len(self._events) + 1, "type": type, "subject": subject,
               "timestamp": self._as_of, "payload": dict(payload or {})}
        self._events.append(evt)
        return evt

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    def memory_traces(self, run_id: str, subject: str, actor: str) -> List[Dict[str, Any]]:
        """Traces neutres, prêtes pour une future ingestion par Memory (11)."""
        return [{
            "kind": "event", "subtype": f"execution.{e['type']}",
            "session_hint": run_id, "actor": actor,
            "timestamp": e["timestamp"],
            "data": {"subject": subject, **e["payload"]},
        } for e in self._events]


__all__ = ["EventLog"]
