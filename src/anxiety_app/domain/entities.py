from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DailyLogEntity:
    id: int
    date: date
    entry_time: datetime
    mood: int
    anxiety: int
    stress: int
    trigger: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ModuleProgressEntity:
    id: int
    module_id: str
    status: str
    progress_percent: int
    completed_at: datetime | None


@dataclass(frozen=True)
class InsightEntity:
    id: int
    generated_at: datetime
    summary_text: str
    raw_data: str


@dataclass(frozen=True)
class ModuleDataEntity:
    id: int
    module_id: str
    data: dict
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ToolEntryEntity:
    id: int
    tool_name: str
    data: dict
    created_at: datetime


@dataclass(frozen=True)
class ToolUsageEntity:
    id: int
    tool_name: str
    used_at: datetime
    metadata: dict


@dataclass(frozen=True)
class UserSettingsEntity:
    id: int
    reminder_time: str
    theme_mode: str
    comfort_mode: bool
    ai_enabled: bool
    onboarding_completed: bool


@dataclass(frozen=True)
class ProgramCompletionSummary:
    completed_modules: int
    total_modules: int
    percent_complete: int


@dataclass(frozen=True)
class EngagementSummary:
    start_date: date
    end_date: date
    active_days: int
    streak_days: int


@dataclass(frozen=True)
class ToolUsageSummary:
    breathcheck_sessions: int
    thought_log_entries: int


@dataclass(frozen=True)
class MilestoneStatus:
    title: str
    description: str
    achieved: bool
    locked: bool = False
    completed_at: datetime | None = None


@dataclass(frozen=True)
class SupportContactEntity:
    id: int
    name: str
    phone: str
    note: str
    created_at: datetime


@dataclass(frozen=True)
class SupportResourceEntity:
    id: int
    title: str
    contact: str
    note: str
    created_at: datetime
