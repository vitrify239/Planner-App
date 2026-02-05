# Planner App (PySide6)

A Windows-friendly planner desktop app built with Python, PySide6, and SQLite.

## Features (MVP)
- Week view (today + next 6 days)
- Month view with selected-day task list
- Tasks and subtasks
- Mark complete/incomplete
- Local SQLite persistence

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m planner_app
```
