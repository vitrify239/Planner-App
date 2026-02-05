from __future__ import annotations

import calendar
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from planner_app.db import TaskRepository
from planner_app.models import Task
from planner_app.services import week_dates
from planner_app.ui.task_dialog import TaskDialog


class MainWindow(QMainWindow):
    def __init__(self, repository: TaskRepository) -> None:
        super().__init__()
        self.repo = repository
        self.setWindowTitle("Planner App")
        self.resize(1200, 700)

        self.tabs = QTabWidget()
        self.week_tab = WeekViewWidget(self.repo)
        self.month_tab = MonthViewWidget(self.repo)
        self.tabs.addTab(self.week_tab, "Week")
        self.tabs.addTab(self.month_tab, "Month")
        self.tabs.setDocumentMode(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)

        self.setCentralWidget(self.tabs)
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f3f5f8;
            }
            QTabWidget::pane {
                border: 1px solid #d8dde6;
                background: #ffffff;
                border-radius: 10px;
                margin-top: 4px;
            }
            QTabBar::tab {
                padding: 8px 14px;
                margin-right: 4px;
                border: 1px solid #d8dde6;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: #e8ecf2;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1f2d3d;
            }
            QGroupBox {
                border: 1px solid #d5dce7;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: 600;
                background: #fbfcfe;
            }
            QGroupBox::title {
                left: 8px;
                padding: 2px 6px;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QTreeWidget, QTableWidget, QCalendarWidget {
                border: 1px solid #d5dce7;
                border-radius: 8px;
                background: white;
            }
            """
        )


class TaskTree(QTreeWidget):
    def __init__(self, repository: TaskRepository, selected_date: date):
        super().__init__()
        self.repo = repository
        self.selected_date = selected_date
        self.setColumnCount(1)
        self.setHeaderLabels(["Tasks"])
        self.itemChanged.connect(self._on_item_changed)

    def load_tasks(self) -> None:
        self.blockSignals(True)
        self.clear()

        tasks = self.repo.list_for_date(self.selected_date)
        by_id = {task.id: task for task in tasks if task.id is not None}
        roots: list[Task] = [t for t in tasks if t.parent_task_id is None]

        for root_task in roots:
            root_item = self._to_item(root_task)
            self.addTopLevelItem(root_item)
            for task in tasks:
                if task.parent_task_id == root_task.id:
                    root_item.addChild(self._to_item(task))

        self.expandAll()
        self.blockSignals(False)

    def _to_item(self, task: Task) -> QTreeWidgetItem:
        item = QTreeWidgetItem([task.title])
        item.setData(0, Qt.ItemDataRole.UserRole, task.id)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(
            0, Qt.CheckState.Checked if task.is_completed else Qt.CheckState.Unchecked
        )
        return item

    def selected_task_id(self) -> int | None:
        current = self.currentItem()
        if current is None:
            return None
        return current.data(0, Qt.ItemDataRole.UserRole)

    def _on_item_changed(self, item: QTreeWidgetItem, _column: int) -> None:
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id is None:
            return
        tasks = self.repo.list_for_date(self.selected_date)
        task = next((t for t in tasks if t.id == task_id), None)
        if task is None:
            return
        task.is_completed = item.checkState(0) == Qt.CheckState.Checked
        self.repo.update(task)


class DayPanel(QGroupBox):
    def __init__(self, repository: TaskRepository, day: date):
        super().__init__(day.strftime("%a %b %d"))
        self.repo = repository
        self.day = day

        self.tree = TaskTree(self.repo, day)
        self.add_btn = QPushButton("Add Task")
        self.add_subtask_btn = QPushButton("Add Subtask")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")

        self.add_btn.clicked.connect(self.add_task)
        self.add_subtask_btn.clicked.connect(self.add_subtask)
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn.clicked.connect(self.delete_task)

        button_row = QHBoxLayout()
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.add_subtask_btn)
        button_row.addWidget(self.edit_btn)
        button_row.addWidget(self.delete_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addLayout(button_row)

        self.refresh()

    def refresh(self) -> None:
        self.tree.load_tasks()

    def _load_task(self, task_id: int) -> Task | None:
        for task in self.repo.list_for_date(self.day):
            if task.id == task_id:
                return task
        return None

    def add_task(self) -> None:
        dialog = TaskDialog(self, default_date=self.day)
        if dialog.exec():
            task = dialog.to_task()
            self.repo.create(task)
            self.refresh()

    def add_subtask(self) -> None:
        parent_id = self.tree.selected_task_id()
        if parent_id is None:
            QMessageBox.information(self, "Select task", "Select a parent task first.")
            return

        dialog = TaskDialog(self, default_date=self.day)
        if dialog.exec():
            task = dialog.to_task(parent_task_id=parent_id)
            self.repo.create(task)
            self.refresh()

    def edit_task(self) -> None:
        task_id = self.tree.selected_task_id()
        if task_id is None:
            return
        existing = self._load_task(task_id)
        if existing is None:
            return

        dialog = TaskDialog(self, task=existing)
        if dialog.exec():
            updated = dialog.to_task(existing=existing)
            self.repo.update(updated)
            self.refresh()

    def delete_task(self) -> None:
        task_id = self.tree.selected_task_id()
        if task_id is None:
            return
        self.repo.delete(task_id)
        self.refresh()


class WeekViewWidget(QWidget):
    def __init__(self, repository: TaskRepository):
        super().__init__()
        self.repo = repository
        self.day_panels: list[DayPanel] = []

        header = QLabel("Today + next 6 days")
        header.setStyleSheet("font-size: 16px; font-weight: 600;")

        panels_row = QHBoxLayout()
        panels_row.setSpacing(12)
        for day in week_dates():
            panel = DayPanel(self.repo, day)
            panel.setMinimumWidth(320)
            self.day_panels.append(panel)
            panels_row.addWidget(panel)

        panels_row.addStretch(1)

        panels_container = QWidget()
        panels_container.setLayout(panels_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(panels_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(header)
        layout.addWidget(scroll)


class MonthTaskGrid(QTableWidget):
    WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, repository: TaskRepository) -> None:
        super().__init__(6, 7)
        self.repo = repository
        self.current_year = date.today().year
        self.current_month = date.today().month
        self._cell_dates: dict[tuple[int, int], date] = {}
        self._selected_day: date | None = None

        self.setHorizontalHeaderLabels(self.WEEKDAY_LABELS)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.setWordWrap(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        for row in range(6):
            self.setRowHeight(row, 120)

    def load_month(self, year: int, month: int, selected_day: date | None = None) -> None:
        self.current_year = year
        self.current_month = month
        self._selected_day = selected_day
        self._cell_dates.clear()
        self.clearContents()

        month_days = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
        for row in range(6):
            week = month_days[row] if row < len(month_days) else []
            for col in range(7):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                if col >= len(week):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    self.setItem(row, col, item)
                    continue

                day = week[col]
                self._cell_dates[(row, col)] = day
                tasks = self.repo.list_for_date(day)
                lines = [f"{day.day}"]
                for task in tasks[:5]:
                    prefix = "✓" if task.is_completed else "•"
                    lines.append(f"{prefix} {task.title}")
                if len(tasks) > 5:
                    lines.append(f"+{len(tasks) - 5} more")
                item.setText("\n".join(lines))

                if day.month != month:
                    item.setForeground(Qt.GlobalColor.darkGray)
                    item.setBackground(Qt.GlobalColor.lightGray)
                if selected_day and day == selected_day:
                    item.setBackground(Qt.GlobalColor.cyan)

                self.setItem(row, col, item)

    def selected_date(self) -> date | None:
        current = self.currentItem()
        if current is None:
            return None
        row = current.row()
        col = current.column()
        return self._cell_dates.get((row, col))


class MonthViewWidget(QWidget):
    def __init__(self, repository: TaskRepository):
        super().__init__()
        self.repo = repository

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self._on_calendar_selection_changed)
        self.month_grid = MonthTaskGrid(self.repo)
        self.month_grid.itemSelectionChanged.connect(self._on_grid_selection_changed)

        self.task_tree = TaskTree(self.repo, self.selected_date())
        self.add_btn = QPushButton("Add Task")
        self.add_subtask_btn = QPushButton("Add Subtask")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")

        self.add_btn.clicked.connect(self.add_task)
        self.add_subtask_btn.clicked.connect(self.add_subtask)
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn.clicked.connect(self.delete_task)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Tasks for selected day"))
        right_layout.addWidget(self.task_tree)

        button_row = QHBoxLayout()
        for btn in [self.add_btn, self.add_subtask_btn, self.edit_btn, self.delete_btn]:
            button_row.addWidget(btn)
        right_layout.addLayout(button_row)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.calendar)
        left_layout.addWidget(QLabel("Month overview"))
        left_layout.addWidget(self.month_grid)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([750, 450])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(splitter)

        self.refresh()

    def selected_date(self) -> date:
        qdate = self.calendar.selectedDate()
        return date(qdate.year(), qdate.month(), qdate.day())

    def _on_calendar_selection_changed(self) -> None:
        self.refresh()

    def _on_grid_selection_changed(self) -> None:
        selected = self.month_grid.selected_date()
        if selected is None:
            return
        self.calendar.setSelectedDate(selected)
        self.task_tree.selected_date = selected
        self.task_tree.load_tasks()

    def refresh(self) -> None:
        selected = self.selected_date()
        self.task_tree.selected_date = selected
        self.task_tree.load_tasks()
        self.month_grid.load_month(selected.year, selected.month, selected)

    def _selected_task(self) -> Task | None:
        task_id = self.task_tree.selected_task_id()
        if task_id is None:
            return None
        tasks = self.repo.list_for_date(self.selected_date())
        return next((t for t in tasks if t.id == task_id), None)

    def add_task(self) -> None:
        dialog = TaskDialog(self, default_date=self.selected_date())
        if dialog.exec():
            self.repo.create(dialog.to_task())
            self.refresh()

    def add_subtask(self) -> None:
        parent_id = self.task_tree.selected_task_id()
        if parent_id is None:
            QMessageBox.information(self, "Select task", "Select a parent task first.")
            return
        dialog = TaskDialog(self, default_date=self.selected_date())
        if dialog.exec():
            self.repo.create(dialog.to_task(parent_task_id=parent_id))
            self.refresh()

    def edit_task(self) -> None:
        existing = self._selected_task()
        if existing is None:
            return
        dialog = TaskDialog(self, task=existing)
        if dialog.exec():
            self.repo.update(dialog.to_task(existing=existing))
            self.refresh()

    def delete_task(self) -> None:
        task_id = self.task_tree.selected_task_id()
        if task_id is None:
            return
        self.repo.delete(task_id)
        self.refresh()
