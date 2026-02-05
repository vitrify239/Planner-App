from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from planner_app.models import Task


class TaskRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    due_date TEXT NOT NULL,
                    is_completed INTEGER NOT NULL DEFAULT 0,
                    parent_task_id INTEGER NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)"
            )

    def list_for_date(self, task_date: date) -> list[Task]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, description, due_date, is_completed, parent_task_id, sort_order
                FROM tasks
                WHERE due_date = ?
                ORDER BY COALESCE(parent_task_id, id), parent_task_id IS NOT NULL, sort_order, id
                """,
                (task_date.isoformat(),),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def create(self, task: Task) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, due_date, is_completed, parent_task_id, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task.title,
                    task.description,
                    task.due_date.isoformat(),
                    int(task.is_completed),
                    task.parent_task_id,
                    task.sort_order,
                ),
            )
            return int(cursor.lastrowid)

    def update(self, task: Task) -> None:
        if task.id is None:
            raise ValueError("Task ID is required for update")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, due_date = ?, is_completed = ?, parent_task_id = ?, sort_order = ?
                WHERE id = ?
                """,
                (
                    task.title,
                    task.description,
                    task.due_date.isoformat(),
                    int(task.is_completed),
                    task.parent_task_id,
                    task.sort_order,
                    task.id,
                ),
            )

    def delete(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            due_date=date.fromisoformat(row["due_date"]),
            is_completed=bool(row["is_completed"]),
            parent_task_id=row["parent_task_id"],
            sort_order=row["sort_order"],
        )
