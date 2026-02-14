from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Callable

from sqlalchemy.orm import Session

import json

from anxiety_app.data.repositories import (
    DailyLogRepository,
    ModuleDataRepository,
    ModuleProgressRepository,
    SupportContactRepository,
    SupportResourceRepository,
    ToolEntryRepository,
    ToolUsageRepository,
    UserSettingsRepository,
)
from anxiety_app.core.security import decrypt_text, encrypt_text
from anxiety_app.domain.analytics import (
    WeeklyAverages,
    compute_current_streak,
    compute_streak_from_dates,
    compute_weekly_averages,
)
from anxiety_app.domain.entities import (
    DailyLogEntity,
    ModuleDataEntity,
    ModuleProgressEntity,
    ProgramCompletionSummary,
    EngagementSummary,
    ToolUsageSummary,
    SupportContactEntity,
    SupportResourceEntity,
    MilestoneStatus,
    ToolEntryEntity,
    ToolUsageEntity,
    UserSettingsEntity,
)

logger = logging.getLogger(__name__)


def _to_daily_entity(model) -> DailyLogEntity:
    return DailyLogEntity(
        id=model.id,
        date=model.date,
        entry_time=model.entry_time,
        mood=model.mood,
        anxiety=model.anxiety,
        stress=model.stress,
        trigger=decrypt_text(model.trigger),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_module_entity(model) -> ModuleProgressEntity:
    return ModuleProgressEntity(
        id=model.id,
        module_id=model.module_id,
        status=model.status,
        progress_percent=model.progress_percent,
        completed_at=model.completed_at,
    )


def _to_module_data_entity(model) -> ModuleDataEntity:
    raw = decrypt_text(model.data_json)
    data = json.loads(raw) if raw else {}
    return ModuleDataEntity(
        id=model.id,
        module_id=model.module_id,
        data=data,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_tool_entry_entity(model) -> ToolEntryEntity:
    raw = decrypt_text(model.data_json)
    data = json.loads(raw) if raw else {}
    return ToolEntryEntity(
        id=model.id,
        tool_name=model.tool_name,
        data=data,
        created_at=model.created_at,
    )


def _to_tool_usage_entity(model) -> ToolUsageEntity:
    raw = decrypt_text(model.metadata_json)
    data = json.loads(raw) if raw else {}
    return ToolUsageEntity(
        id=model.id,
        tool_name=model.tool_name,
        used_at=model.used_at,
        metadata=data,
    )


def _to_user_settings_entity(model) -> UserSettingsEntity:
    return UserSettingsEntity(
        id=model.id,
        reminder_time=model.reminder_time,
        theme_mode=model.theme_mode,
        comfort_mode=model.comfort_mode,
        ai_enabled=model.ai_enabled,
        onboarding_completed=model.onboarding_completed,
    )


def _to_support_contact_entity(model) -> SupportContactEntity:
    return SupportContactEntity(
        id=model.id,
        name=model.name,
        phone=model.phone,
        note=model.note,
        created_at=model.created_at,
    )


def _to_support_resource_entity(model) -> SupportResourceEntity:
    return SupportResourceEntity(
        id=model.id,
        title=model.title,
        contact=model.contact,
        note=model.note,
        created_at=model.created_at,
    )


class TrackingService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        log_repo: DailyLogRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._log_repo = log_repo or DailyLogRepository()

    def create_or_update_daily_log(
        self,
        log_date: date,
        mood: int,
        anxiety: int,
        stress: int,
        trigger: str,
        entry_time: datetime,
    ) -> tuple[DailyLogEntity, bool]:
        with self._session_factory() as session:
            entry, created = self._log_repo.upsert_by_date(
                session,
                log_date,
                mood,
                anxiety,
                stress,
                encrypt_text(trigger),
                entry_time,
            )
        logger.info(
            "%s daily log for %s",
            "Created" if created else "Updated",
            log_date.isoformat(),
        )
        return _to_daily_entity(entry), created

    def get_daily_log(self, log_date: date) -> DailyLogEntity | None:
        with self._session_factory() as session:
            entry = self._log_repo.get_by_date(session, log_date)
        return _to_daily_entity(entry) if entry else None

    def recent_logs(self, limit: int = 10) -> list[DailyLogEntity]:
        with self._session_factory() as session:
            logs = self._log_repo.list_recent(session, limit)
        return [_to_daily_entity(log) for log in logs]

    def weekly_averages(self) -> WeeklyAverages | None:
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        with self._session_factory() as session:
            logs = self._log_repo.list_by_range(session, start_date, end_date)
        entities = [_to_daily_entity(log) for log in logs]
        return compute_weekly_averages(entities)

    def current_streak(self) -> int:
        with self._session_factory() as session:
            logs = self._log_repo.list_recent(session, limit=30)
        entities = [_to_daily_entity(log) for log in logs]
        return compute_current_streak(entities)


class LearningService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        module_repo: ModuleProgressRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._module_repo = module_repo or ModuleProgressRepository()

    def update_progress(
        self,
        module_id: str,
        status: str,
        progress_percent: int,
        completed_at: datetime | None = None,
    ) -> ModuleProgressEntity:
        with self._session_factory() as session:
            entry = self._module_repo.upsert(
                session, module_id, status, progress_percent, completed_at
            )
        logger.info("Updated module %s to %s", module_id, status)
        return _to_module_entity(entry)

    def list_progress(self) -> list[ModuleProgressEntity]:
        with self._session_factory() as session:
            entries = self._module_repo.list_all(session)
        return [_to_module_entity(entry) for entry in entries]

    def get_progress(self, module_id: str) -> ModuleProgressEntity | None:
        with self._session_factory() as session:
            entry = self._module_repo.get_by_module(session, module_id)
        return _to_module_entity(entry) if entry else None


class ToolUsageService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        usage_repo: ToolUsageRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._usage_repo = usage_repo or ToolUsageRepository()

    def record_usage(self, tool_name: str, metadata: dict) -> ToolUsageEntity:
        data_json = encrypt_text(json.dumps(metadata))
        with self._session_factory() as session:
            entry = self._usage_repo.create(session, tool_name, data_json)
        return _to_tool_usage_entity(entry)

    def list_usage(self) -> list[ToolUsageEntity]:
        with self._session_factory() as session:
            entries = self._usage_repo.list_all(session)
        return [_to_tool_usage_entity(entry) for entry in entries]


class ProgressService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        module_repo: ModuleProgressRepository | None = None,
        module_data_repo: ModuleDataRepository | None = None,
        tool_usage_repo: ToolUsageRepository | None = None,
        tool_entry_repo: ToolEntryRepository | None = None,
        log_repo: DailyLogRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._module_repo = module_repo or ModuleProgressRepository()
        self._module_data_repo = module_data_repo or ModuleDataRepository()
        self._tool_usage_repo = tool_usage_repo or ToolUsageRepository()
        self._tool_entry_repo = tool_entry_repo or ToolEntryRepository()
        self._log_repo = log_repo or DailyLogRepository()

    def program_completion(self, module_ids: list[str]) -> ProgramCompletionSummary:
        with self._session_factory() as session:
            entries = self._module_repo.list_all(session)
        total = len(module_ids)
        completed = sum(
            1
            for entry in entries
            if entry.module_id in module_ids and entry.status.upper() in {"COMPLETE", "COMPLETED"}
        )
        percent = int((completed / total) * 100) if total else 0
        return ProgramCompletionSummary(completed, total, percent)

    def tool_usage_summary(self) -> ToolUsageSummary:
        with self._session_factory() as session:
            usage_entries = self._tool_usage_repo.list_all(session)
            tool_entries = self._tool_entry_repo.list_all(session)
        breathcheck_sessions = sum(
            1 for entry in usage_entries if entry.tool_name == "breathcheck_tool"
        )
        thought_log_entries = sum(
            1 for entry in tool_entries if entry.tool_name == "thought_log"
        )
        return ToolUsageSummary(
            breathcheck_sessions=breathcheck_sessions,
            thought_log_entries=thought_log_entries,
        )

    def engagement_summary(self, days: int = 7) -> EngagementSummary:
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        active_dates: set[date] = set()
        with self._session_factory() as session:
            for entry in self._tool_usage_repo.list_all(session):
                active_dates.add(entry.used_at.date())
            for entry in self._tool_entry_repo.list_all(session):
                active_dates.add(entry.created_at.date())
            for entry in self._module_data_repo.list_all(session):
                active_dates.add(entry.updated_at.date())
            for entry in self._log_repo.list_all(session):
                active_dates.add(entry.date)
        active_days = len({d for d in active_dates if start_date <= d <= end_date})
        streak_days = compute_streak_from_dates(active_dates)
        return EngagementSummary(
            start_date=start_date,
            end_date=end_date,
            active_days=active_days,
            streak_days=streak_days,
        )

    def milestone_statuses(self, module_ids: list[str]) -> list[MilestoneStatus]:
        completion = self.program_completion(module_ids)
        usage = self.tool_usage_summary()
        engagement = self.engagement_summary()
        with self._session_factory() as session:
            progress_entries = {
                entry.module_id: entry for entry in self._module_repo.list_all(session)
            }

        milestones: list[MilestoneStatus] = []
        prev_complete = True
        for i, module_id in enumerate(module_ids, start=1):
            entry = progress_entries.get(module_id)
            status = entry.status.upper() if entry else "LOCKED"
            achieved = status in {"COMPLETE", "COMPLETED"}
            locked = (not prev_complete) and (not achieved)
            milestones.append(
                MilestoneStatus(
                    title=f"Module {i} completed",
                    description=f"Complete Module {i}.",
                    achieved=achieved,
                    locked=locked,
                    completed_at=entry.completed_at if achieved and entry else None,
                )
            )
            prev_complete = achieved

        milestones.extend(
            [
                MilestoneStatus(
                    "Relaxation starter",
                    "Use the BreathCheck tool once.",
                    usage.breathcheck_sessions >= 1,
                ),
                MilestoneStatus(
                    "Thought log starter",
                    "Save your first thought log.",
                    usage.thought_log_entries >= 1,
                ),
                MilestoneStatus(
                    "Weekly engagement",
                    "Engage with BreathCheck on 4 days this week.",
                    engagement.active_days >= 4,
                ),
                MilestoneStatus(
                    "Building streak",
                    "Reach a 3-day engagement streak.",
                    engagement.streak_days >= 3,
                ),
                MilestoneStatus(
                    "Program complete",
                    "Complete all 6 modules.",
                    completion.completed_modules == completion.total_modules and completion.total_modules > 0,
                ),
            ]
        )
        return milestones


class UserSettingsService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        settings_repo: UserSettingsRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings_repo = settings_repo or UserSettingsRepository()

    def get_settings(self) -> UserSettingsEntity:
        with self._session_factory() as session:
            entry = self._settings_repo.get(session)
            if not entry:
                entry = self._settings_repo.save(
                    session,
                    {
                        "reminder_time": "Morning",
                        "theme_mode": "light",
                        "comfort_mode": False,
                        "ai_enabled": True,
                        "onboarding_completed": False,
                    },
                )
        return _to_user_settings_entity(entry)

    def update_settings(self, payload: dict) -> UserSettingsEntity:
        with self._session_factory() as session:
            entry = self._settings_repo.save(session, payload)
        return _to_user_settings_entity(entry)


class ModuleDataService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        module_repo: ModuleDataRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._module_repo = module_repo or ModuleDataRepository()

    def get_module_data(self, module_id: str) -> ModuleDataEntity | None:
        with self._session_factory() as session:
            entry = self._module_repo.get_by_module(session, module_id)
        return _to_module_data_entity(entry) if entry else None

    def update_module_data(self, module_id: str, payload: dict) -> ModuleDataEntity:
        existing = self.get_module_data(module_id)
        data = existing.data if existing else {}
        data.update(payload)
        data_json = encrypt_text(json.dumps(data))
        with self._session_factory() as session:
            entry = self._module_repo.save_or_update(session, module_id, data_json)
        return _to_module_data_entity(entry)

    def list_module_data(self) -> list[ModuleDataEntity]:
        with self._session_factory() as session:
            entries = self._module_repo.list_all(session)
        return [_to_module_data_entity(entry) for entry in entries]


class ToolService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        tool_repo: ToolEntryRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._tool_repo = tool_repo or ToolEntryRepository()

    def create_entry(self, tool_name: str, payload: dict) -> ToolEntryEntity:
        data_json = encrypt_text(json.dumps(payload))
        with self._session_factory() as session:
            entry = self._tool_repo.create(session, tool_name, data_json)
        return _to_tool_entry_entity(entry)

    def update_entry(self, entry_id: int, payload: dict) -> ToolEntryEntity:
        data_json = encrypt_text(json.dumps(payload))
        with self._session_factory() as session:
            entry = self._tool_repo.update(session, entry_id, data_json)
        return _to_tool_entry_entity(entry)

    def list_entries(self) -> list[ToolEntryEntity]:
        with self._session_factory() as session:
            entries = self._tool_repo.list_all(session)
        return [_to_tool_entry_entity(entry) for entry in entries]


class SupportService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        contact_repo: SupportContactRepository | None = None,
        resource_repo: SupportResourceRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._contact_repo = contact_repo or SupportContactRepository()
        self._resource_repo = resource_repo or SupportResourceRepository()

    def list_contacts(self) -> list[SupportContactEntity]:
        with self._session_factory() as session:
            entries = self._contact_repo.list_all(session)
        return [_to_support_contact_entity(entry) for entry in entries]

    def add_contact(self, name: str, phone: str, note: str) -> SupportContactEntity:
        with self._session_factory() as session:
            entry = self._contact_repo.create(session, name, phone, note)
        return _to_support_contact_entity(entry)

    def delete_contact(self, entry_id: int) -> None:
        with self._session_factory() as session:
            self._contact_repo.delete(session, entry_id)

    def list_resources(self) -> list[SupportResourceEntity]:
        with self._session_factory() as session:
            entries = self._resource_repo.list_all(session)
        return [_to_support_resource_entity(entry) for entry in entries]

    def add_resource(self, title: str, contact: str, note: str) -> SupportResourceEntity:
        with self._session_factory() as session:
            entry = self._resource_repo.create(session, title, contact, note)
        return _to_support_resource_entity(entry)

    def delete_resource(self, entry_id: int) -> None:
        with self._session_factory() as session:
            self._resource_repo.delete(session, entry_id)
