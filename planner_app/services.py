from __future__ import annotations

from datetime import date, timedelta


def week_dates(start: date | None = None) -> list[date]:
    base = start or date.today()
    return [base + timedelta(days=offset) for offset in range(7)]
