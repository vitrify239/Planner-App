from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from planner_app.db import TaskRepository
from planner_app.ui.main_window import MainWindow


def app_db_path() -> Path:
    return Path.home() / ".planner_app" / "planner.sqlite3"


def main() -> int:
    app = QApplication(sys.argv)
    repo = TaskRepository(app_db_path())
    window = MainWindow(repo)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
