# Planner App (PySide6)

A lightweight desktop planner app built with **Python + PySide6 + SQLite**.

This version includes:
- **Week view** (today + next 6 days)
- **Month view** (calendar + selected day tasks)
- **Tasks and subtasks**
- Mark complete/incomplete
- Local storage in SQLite

---

## 1) Prerequisites

- Python **3.10+** installed
- `pip` available
- Windows, macOS, or Linux (UI target is Windows-friendly)

Check your Python version:

```bash
python --version
```

---

## 2) Install and run

From the project root:

```bash
python -m venv .venv
```

Activate the virtual environment:

### Windows (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows (cmd)
```cmd
.venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch the app:

```bash
python -m planner_app
```

---

## 3) Quick walkthrough

### Week tab
- The app opens to **Week** by default.
- You’ll see 7 day panels: **today + next 6 days**.
- For each day:
  - **Add Task** creates a top-level task
  - **Add Subtask** creates a subtask under the currently selected task
  - **Edit** updates the selected task
  - **Delete** removes the selected task
- Use the checkbox beside each task to mark it complete.

### Month tab
- Use the calendar to pick a day.
- The right panel shows tasks for the selected date.
- Use the same **Add/Edit/Delete/Subtask** controls.

---

## 4) Where data is stored

Tasks are stored locally in:

```text
~/.planner_app/planner.sqlite3
```

On Windows, that resolves to your user profile directory (for example, `C:\Users\<you>\.planner_app\planner.sqlite3`).

---

## 5) Common issues

### `No module named PySide6`
Your dependencies are not installed in the active environment.

Fix:
```bash
pip install -r requirements.txt
```

### Virtual environment won’t activate on PowerShell
PowerShell execution policy may block scripts.

Temporary fix in the current shell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then run activation again:
```powershell
.\.venv\Scripts\Activate.ps1
```

### App launches but no tasks appear
That is expected for first run—add tasks from either Week or Month view.

---

## 6) Developer quick check

Run a syntax check:

```bash
python -m compileall planner_app
```
