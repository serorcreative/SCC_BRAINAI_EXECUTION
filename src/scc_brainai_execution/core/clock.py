"""Primitives déterministes : sérialisation canonique et empreintes.

L'exécution est **déterministe** : identifiants et empreintes dérivent du contenu ;
le Runtime est piloté avec une horloge injectée. Stdlib pur.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def short_id(prefix: str, obj: Any) -> str:
    return f"{prefix}_{digest(obj)[:12]}"


__all__ = ["canonical", "digest", "short_id"]
