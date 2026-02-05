from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Task:
    id: int | None
    title: str
    due_date: date
    description: str = ""
    is_completed: bool = False
    parent_task_id: int | None = None
    sort_order: int = 0
