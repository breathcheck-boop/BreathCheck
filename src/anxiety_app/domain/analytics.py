from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean

from anxiety_app.domain.entities import DailyLogEntity


@dataclass(frozen=True)
class WeeklyAverages:
    start_date: date
    end_date: date
    mood_avg: float
    anxiety_avg: float
    stress_avg: float


def compute_weekly_averages(logs: list[DailyLogEntity]) -> WeeklyAverages | None:
    if not logs:
        return None
    start_date = logs[0].date
    end_date = logs[-1].date
    mood_avg = mean([log.mood for log in logs])
    anxiety_avg = mean([log.anxiety for log in logs])
    stress_avg = mean([log.stress for log in logs])
    return WeeklyAverages(
        start_date=start_date,
        end_date=end_date,
        mood_avg=mood_avg,
        anxiety_avg=anxiety_avg,
        stress_avg=stress_avg,
    )


def compute_current_streak(logs: list[DailyLogEntity]) -> int:
    if not logs:
        return 0
    dates = {log.date for log in logs}
    streak = 0
    current = date.today()
    while current in dates:
        streak += 1
        current = current.fromordinal(current.toordinal() - 1)
    return streak


def compute_streak_from_dates(dates: set[date]) -> int:
    if not dates:
        return 0
    streak = 0
    current = date.today()
    while current in dates:
        streak += 1
        current = current.fromordinal(current.toordinal() - 1)
    return streak
