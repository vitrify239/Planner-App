from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
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

        self.setCentralWidget(self.tabs)


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
        for day in week_dates():
            panel = DayPanel(self.repo, day)
            self.day_panels.append(panel)
            panels_row.addWidget(panel)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addLayout(panels_row)


class MonthViewWidget(QWidget):
    def __init__(self, repository: TaskRepository):
        super().__init__()
        self.repo = repository

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.refresh)

        self.task_tree = TaskTree(self.repo, date.today())
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
        right_layout.addWidget(QLabel("Tasks for selected day"))
        right_layout.addWidget(self.task_tree)

        button_row = QHBoxLayout()
        for btn in [self.add_btn, self.add_subtask_btn, self.edit_btn, self.delete_btn]:
            button_row.addWidget(btn)
        right_layout.addLayout(button_row)

        splitter = QSplitter()
        splitter.addWidget(self.calendar)
        splitter.addWidget(right)
        splitter.setSizes([500, 700])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self.refresh()

    def selected_date(self) -> date:
        qdate = self.calendar.selectedDate()
        return date(qdate.year(), qdate.month(), qdate.day())

    def refresh(self) -> None:
        self.task_tree.selected_date = self.selected_date()
        self.task_tree.load_tasks()

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
