from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
)

from planner_app.models import Task


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task | None = None, default_date: date | None = None):
        super().__init__(parent)
        self.setWindowTitle("Task")

        self.title_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()
        self.due_date_edit = QDateEdit(calendarPopup=True)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.completed_checkbox = QCheckBox("Completed")

        if task is not None:
            self.title_edit.setText(task.title)
            self.description_edit.setPlainText(task.description)
            self.due_date_edit.setDate(
                QDate(task.due_date.year, task.due_date.month, task.due_date.day)
            )
            self.completed_checkbox.setChecked(task.is_completed)
        else:
            selected_date = default_date or date.today()
            self.due_date_edit.setDate(
                QDate(selected_date.year, selected_date.month, selected_date.day)
            )

        form = QFormLayout()
        form.addRow("Title", self.title_edit)
        form.addRow("Description", self.description_edit)
        form.addRow("Due Date", self.due_date_edit)
        form.addRow("", self.completed_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def to_task(self, existing: Task | None = None, parent_task_id: int | None = None) -> Task:
        qdate = self.due_date_edit.date()
        due_date = date(qdate.year(), qdate.month(), qdate.day())
        return Task(
            id=existing.id if existing else None,
            title=self.title_edit.text().strip() or "Untitled Task",
            description=self.description_edit.toPlainText().strip(),
            due_date=due_date,
            is_completed=self.completed_checkbox.isChecked(),
            parent_task_id=parent_task_id if existing is None else existing.parent_task_id,
            sort_order=existing.sort_order if existing else 0,
        )
