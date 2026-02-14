from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Callable, Iterable

from sqlalchemy import delete
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
from anxiety_app.core.security import delete_encryption_key, decrypt_text, ensure_encryption_key, delete_master_password
from anxiety_app.services.ai_client import AIClient

logger = logging.getLogger(__name__)


class SettingsService:
    def __init__(
        self, session_factory: Callable[[], Session], ai_client: AIClient
    ) -> None:
        self._session_factory = session_factory
        self._ai_client = ai_client
        self.service_name = ai_client.service_name

    def delete_all_data(self) -> None:
        with self._session_factory() as session:
            session.execute(delete(DailyLog))
            session.execute(delete(ModuleProgress))
            session.execute(delete(InsightCache))
            session.execute(delete(UserModuleData))
            session.execute(delete(ToolEntry))
            session.execute(delete(ToolUsage))
            session.execute(delete(UserSettings))
            session.execute(delete(SupportContact))
            session.execute(delete(SupportResource))
            session.commit()
        logger.info("Deleted all local data")

    def check_api_key_status(self) -> str:
        ok, message = self._ai_client.validate_key()
        return message if ok else message

    def delete_account(self) -> None:
        self.delete_all_data()
        delete_encryption_key(self.service_name)
        delete_master_password(self.service_name)
        logger.info("Deleted account data and master password")

    def reset_progress(self) -> None:
        with self._session_factory() as session:
            session.execute(delete(ModuleProgress))
            session.execute(delete(UserModuleData))
            session.commit()
        logger.info("Reset module progress and learning data")

    def encryption_status(self) -> tuple[bool, str]:
        enabled = ensure_encryption_key(self.service_name)
        if enabled:
            return True, "Local encryption is enabled. Your data is stored encrypted on this device."
        return False, "Local encryption is unavailable (keyring not accessible)."

    def export_all_data(self, export_format: str, path: Path) -> list[Path]:
        data = self._collect_export_data()
        export_format = export_format.lower()
        if export_format == "json":
            return [self._export_json(data, path)]
        if export_format == "csv":
            return self._export_csv_bundle(data, path)
        if export_format == "excel":
            return [self._export_excel(data, path)]
        raise ValueError("Unsupported export format")

    def _collect_export_data(self) -> dict[str, list[dict]]:
        with self._session_factory() as session:
            logs = session.query(DailyLog).order_by(DailyLog.date.asc()).all()
            progress = session.query(ModuleProgress).order_by(ModuleProgress.module_id.asc()).all()
            module_data = session.query(UserModuleData).order_by(UserModuleData.module_id.asc()).all()
            tool_entries = session.query(ToolEntry).order_by(ToolEntry.created_at.asc()).all()
            tool_usage = session.query(ToolUsage).order_by(ToolUsage.used_at.asc()).all()
            settings = session.query(UserSettings).order_by(UserSettings.id.asc()).all()
            insights = session.query(InsightCache).order_by(InsightCache.generated_at.asc()).all()
            support_contacts = session.query(SupportContact).order_by(SupportContact.created_at.asc()).all()
            support_resources = session.query(SupportResource).order_by(SupportResource.created_at.asc()).all()

        def iso(value) -> str:
            return value.isoformat() if value else ""

        logs_rows = [
            {
                "id": entry.id,
                "date": iso(entry.date),
                "entry_time": iso(entry.entry_time),
                "mood": entry.mood,
                "anxiety": entry.anxiety,
                "stress": entry.stress,
                "trigger": decrypt_text(entry.trigger),
                "created_at": iso(entry.created_at),
                "updated_at": iso(entry.updated_at),
            }
            for entry in logs
        ]
        progress_rows = [
            {
                "id": entry.id,
                "module_id": entry.module_id,
                "status": entry.status,
                "progress_percent": entry.progress_percent,
                "completed_at": iso(entry.completed_at),
            }
            for entry in progress
        ]
        module_rows = []
        for entry in module_data:
            raw = decrypt_text(entry.data_json)
            payload = json.loads(raw) if raw else {}
            module_rows.append(
                {
                    "id": entry.id,
                    "module_id": entry.module_id,
                    "data": payload,
                    "created_at": iso(entry.created_at),
                    "updated_at": iso(entry.updated_at),
                }
            )
        tool_rows = []
        for entry in tool_entries:
            raw = decrypt_text(entry.data_json)
            payload = json.loads(raw) if raw else {}
            tool_rows.append(
                {
                    "id": entry.id,
                    "tool_name": entry.tool_name,
                    "data": payload,
                    "created_at": iso(entry.created_at),
                }
            )
        usage_rows = []
        for entry in tool_usage:
            raw = decrypt_text(entry.metadata_json)
            payload = json.loads(raw) if raw else {}
            usage_rows.append(
                {
                    "id": entry.id,
                    "tool_name": entry.tool_name,
                    "used_at": iso(entry.used_at),
                    "metadata": payload,
                }
            )
        settings_rows = [
            {
                "id": entry.id,
                "reminder_time": entry.reminder_time,
                "theme_mode": entry.theme_mode,
                "comfort_mode": entry.comfort_mode,
                "ai_enabled": entry.ai_enabled,
                "onboarding_completed": entry.onboarding_completed,
            }
            for entry in settings
        ]
        insight_rows = []
        for entry in insights:
            insight_rows.append(
                {
                    "id": entry.id,
                    "generated_at": iso(entry.generated_at),
                    "summary_text": decrypt_text(entry.summary_text),
                    "raw_data": decrypt_text(entry.raw_data),
                }
            )
        contacts_rows = [
            {
                "id": entry.id,
                "name": entry.name,
                "phone": entry.phone,
                "note": entry.note,
                "created_at": iso(entry.created_at),
            }
            for entry in support_contacts
        ]
        resources_rows = [
            {
                "id": entry.id,
                "title": entry.title,
                "contact": entry.contact,
                "note": entry.note,
                "created_at": iso(entry.created_at),
            }
            for entry in support_resources
        ]
        return {
            "daily_logs": logs_rows,
            "module_progress": progress_rows,
            "module_data": module_rows,
            "tool_entries": tool_rows,
            "tool_usage": usage_rows,
            "user_settings": settings_rows,
            "insights": insight_rows,
            "support_contacts": contacts_rows,
            "support_resources": resources_rows,
        }

    def _export_json(self, data: dict[str, list[dict]], path: Path) -> Path:
        target = path if path.suffix else path.with_suffix(".json")
        target.write_text(json.dumps(data, indent=2))
        return target

    def _export_csv_bundle(self, data: dict[str, list[dict]], path: Path) -> list[Path]:
        base = path
        if base.suffix:
            base = base.with_suffix("")
        output_paths: list[Path] = []
        for name, rows in data.items():
            target = base.with_name(f"{base.name}_{name}.csv")
            output_paths.append(target)
            if not rows:
                target.write_text("")
                continue
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: self._normalize_value(v) for k, v in row.items()})
        return output_paths

    def _export_excel(self, data: dict[str, list[dict]], path: Path) -> Path:
        try:
            from openpyxl import Workbook
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Excel export requires openpyxl.") from exc
        target = path if path.suffix else path.with_suffix(".xlsx")
        workbook = Workbook()
        workbook.remove(workbook.active)
        for name, rows in data.items():
            sheet = workbook.create_sheet(title=name[:31])
            if not rows:
                continue
            headers = list(rows[0].keys())
            sheet.append(headers)
            for row in rows:
                sheet.append([self._normalize_value(row.get(header)) for header in headers])
        workbook.save(target)
        return target

    def _normalize_value(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
