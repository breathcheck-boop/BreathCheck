from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from anxiety_app.data.models import (
    DailyLog,
    InsightCache,
    ModuleProgress,
    SupportContact,
    SupportResource,
    ToolEntry,
    ToolUsage,
    UserModuleData,
    UserSettings,
)


class DailyLogRepository:
    def create(
        self,
        session: Session,
        log_date: date,
        mood: int,
        anxiety: int,
        stress: int,
        trigger: str,
        entry_time: datetime,
    ) -> DailyLog:
        entry = DailyLog(
            date=log_date,
            mood=mood,
            anxiety=anxiety,
            stress=stress,
            trigger=trigger,
            entry_time=entry_time,
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def get_by_date(self, session: Session, log_date: date) -> Optional[DailyLog]:
        stmt = select(DailyLog).where(DailyLog.date == log_date)
        return session.execute(stmt).scalars().first()

    def upsert_by_date(
        self,
        session: Session,
        log_date: date,
        mood: int,
        anxiety: int,
        stress: int,
        trigger: str,
        entry_time: datetime,
    ) -> tuple[DailyLog, bool]:
        existing = self.get_by_date(session, log_date)
        if existing:
            existing.mood = mood
            existing.anxiety = anxiety
            existing.stress = stress
            existing.trigger = trigger
            existing.entry_time = entry_time
            session.commit()
            session.refresh(existing)
            return existing, False
        entry = self.create(
            session, log_date, mood, anxiety, stress, trigger, entry_time
        )
        return entry, True

    def list_recent(self, session: Session, limit: int = 10) -> list[DailyLog]:
        stmt = (
            select(DailyLog)
            .order_by(DailyLog.date.desc(), DailyLog.entry_time.desc())
            .limit(limit)
        )
        return list(session.execute(stmt).scalars())

    def list_by_range(
        self, session: Session, start_date: date, end_date: date
    ) -> list[DailyLog]:
        stmt = (
            select(DailyLog)
            .where(DailyLog.date >= start_date, DailyLog.date <= end_date)
            .order_by(DailyLog.date.asc())
        )
        return list(session.execute(stmt).scalars())

    def list_all(self, session: Session) -> list[DailyLog]:
        stmt = select(DailyLog).order_by(DailyLog.date.asc(), DailyLog.entry_time.asc())
        return list(session.execute(stmt).scalars())


class ModuleProgressRepository:
    def get_by_module(
        self, session: Session, module_id: str
    ) -> Optional[ModuleProgress]:
        stmt = select(ModuleProgress).where(ModuleProgress.module_id == module_id)
        return session.execute(stmt).scalars().first()

    def list_all(self, session: Session) -> list[ModuleProgress]:
        stmt = select(ModuleProgress).order_by(ModuleProgress.module_id.asc())
        return list(session.execute(stmt).scalars())

    def upsert(
        self,
        session: Session,
        module_id: str,
        status: str,
        progress_percent: int,
        completed_at: datetime | None = None,
    ) -> ModuleProgress:
        existing = self.get_by_module(session, module_id)
        if existing:
            existing.status = status
            existing.progress_percent = progress_percent
            if completed_at is not None:
                existing.completed_at = completed_at
            session.commit()
            session.refresh(existing)
            return existing
        entry = ModuleProgress(
            module_id=module_id,
            status=status,
            progress_percent=progress_percent,
            completed_at=completed_at,
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry


class InsightCacheRepository:
    def latest(self, session: Session) -> Optional[InsightCache]:
        stmt = select(InsightCache).order_by(InsightCache.generated_at.desc()).limit(1)
        return session.execute(stmt).scalars().first()

    def create(self, session: Session, summary_text: str, raw_data: str) -> InsightCache:
        entry = InsightCache(summary_text=summary_text, raw_data=raw_data)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def list_recent(self, session: Session, limit: int = 5) -> Iterable[InsightCache]:
        stmt = (
            select(InsightCache).order_by(InsightCache.generated_at.desc()).limit(limit)
        )
        return list(session.execute(stmt).scalars())


class ModuleDataRepository:
    def get_by_module(self, session: Session, module_id: str) -> Optional[UserModuleData]:
        stmt = select(UserModuleData).where(UserModuleData.module_id == module_id)
        return session.execute(stmt).scalars().first()

    def list_all(self, session: Session) -> list[UserModuleData]:
        stmt = select(UserModuleData).order_by(UserModuleData.module_id.asc())
        return list(session.execute(stmt).scalars())

    def save_or_update(
        self, session: Session, module_id: str, data_json: str
    ) -> UserModuleData:
        existing = self.get_by_module(session, module_id)
        if existing:
            existing.data_json = data_json
            session.commit()
            session.refresh(existing)
            return existing
        entry = UserModuleData(module_id=module_id, data_json=data_json)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry


class ToolEntryRepository:
    def create(self, session: Session, tool_name: str, data_json: str) -> ToolEntry:
        entry = ToolEntry(tool_name=tool_name, data_json=data_json)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def update(self, session: Session, entry_id: int, data_json: str) -> ToolEntry:
        entry = session.get(ToolEntry, entry_id)
        if not entry:
            raise ValueError("Tool entry not found")
        entry.data_json = data_json
        session.commit()
        session.refresh(entry)
        return entry

    def list_all(self, session: Session) -> list[ToolEntry]:
        stmt = select(ToolEntry).order_by(ToolEntry.created_at.asc())
        return list(session.execute(stmt).scalars())


class ToolUsageRepository:
    def create(self, session: Session, tool_name: str, metadata_json: str) -> ToolUsage:
        entry = ToolUsage(tool_name=tool_name, metadata_json=metadata_json)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def list_all(self, session: Session) -> list[ToolUsage]:
        stmt = select(ToolUsage).order_by(ToolUsage.used_at.asc())
        return list(session.execute(stmt).scalars())


class UserSettingsRepository:
    def get(self, session: Session) -> Optional[UserSettings]:
        stmt = select(UserSettings).order_by(UserSettings.id.asc()).limit(1)
        return session.execute(stmt).scalars().first()

    def save(self, session: Session, payload: dict) -> UserSettings:
        existing = self.get(session)
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            session.commit()
            session.refresh(existing)
            return existing
        entry = UserSettings(**payload)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry


class SupportContactRepository:
    def list_all(self, session: Session) -> list[SupportContact]:
        stmt = select(SupportContact).order_by(SupportContact.created_at.desc())
        return list(session.execute(stmt).scalars())

    def create(self, session: Session, name: str, phone: str, note: str) -> SupportContact:
        entry = SupportContact(name=name, phone=phone, note=note)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def delete(self, session: Session, entry_id: int) -> None:
        entry = session.get(SupportContact, entry_id)
        if not entry:
            return
        session.delete(entry)
        session.commit()


class SupportResourceRepository:
    def list_all(self, session: Session) -> list[SupportResource]:
        stmt = select(SupportResource).order_by(SupportResource.created_at.desc())
        return list(session.execute(stmt).scalars())

    def create(
        self, session: Session, title: str, contact: str, note: str
    ) -> SupportResource:
        entry = SupportResource(title=title, contact=contact, note=note)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def delete(self, session: Session, entry_id: int) -> None:
        entry = session.get(SupportResource, entry_id)
        if not entry:
            return
        session.delete(entry)
        session.commit()
