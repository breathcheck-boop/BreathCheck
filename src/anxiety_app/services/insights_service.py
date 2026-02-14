from __future__ import annotations

import json
import logging
from typing import Callable

from sqlalchemy.orm import Session

from anxiety_app.data.repositories import (
    DailyLogRepository,
    InsightCacheRepository,
    ModuleProgressRepository,
    ToolUsageRepository,
)
from anxiety_app.domain.analytics import compute_weekly_averages
from anxiety_app.domain.entities import DailyLogEntity, InsightEntity
from anxiety_app.domain.services import ModuleDataService, ToolService, UserSettingsService
from anxiety_app.services.ai_client import AIClient
from anxiety_app.core.security import decrypt_text, encrypt_text

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


def _to_insight_entity(model) -> InsightEntity:
    return InsightEntity(
        id=model.id,
        generated_at=model.generated_at,
        summary_text=decrypt_text(model.summary_text),
        raw_data=decrypt_text(model.raw_data),
    )


class InsightsService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        ai_client: AIClient,
        log_repo: DailyLogRepository | None = None,
        insights_repo: InsightCacheRepository | None = None,
        module_data_service: ModuleDataService | None = None,
        progress_repo: ModuleProgressRepository | None = None,
        tool_service: ToolService | None = None,
        tool_usage_repo: ToolUsageRepository | None = None,
        user_settings_service: UserSettingsService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._ai_client = ai_client
        self._log_repo = log_repo or DailyLogRepository()
        self._insights_repo = insights_repo or InsightCacheRepository()
        self._module_data_service = module_data_service
        self._progress_repo = progress_repo or ModuleProgressRepository()
        self._tool_service = tool_service
        self._tool_usage_repo = tool_usage_repo or ToolUsageRepository()
        self._user_settings_service = user_settings_service

    def generate(self) -> InsightEntity:
        with self._session_factory() as session:
            logs = self._log_repo.list_all(session)
        entities = [_to_daily_entity(log) for log in logs]
        averages = compute_weekly_averages(entities)
        module_entries = (
            self._module_data_service.list_module_data()
            if self._module_data_service
            else []
        )
        with self._session_factory() as session:
            progress_entries = self._progress_repo.list_all(session)
            tool_usage_entries = self._tool_usage_repo.list_all(session)
        averages_payload = None
        if averages:
            averages_payload = {
                "start_date": averages.start_date.isoformat(),
                "end_date": averages.end_date.isoformat(),
                "mood_avg": averages.mood_avg,
                "anxiety_avg": averages.anxiety_avg,
                "stress_avg": averages.stress_avg,
            }
        tool_entries = self._tool_service.list_entries() if self._tool_service else []
        thought_logs = [
            entry for entry in tool_entries if entry.tool_name == "thought_log"
        ]
        prompt_payload = {
            "recent_logs": [
                {
                    "date": log.date.isoformat(),
                    "time": (log.entry_time or log.created_at).isoformat(),
                    "mood": log.mood,
                    "anxiety": log.anxiety,
                    "stress": log.stress,
                    "trigger": log.trigger,
                }
                for log in entities
            ],
            "weekly_averages": averages_payload,
            "module_data": {entry.module_id: entry.data for entry in module_entries},
            "tool_entries": [
                {
                    "tool_name": entry.tool_name,
                    "created_at": entry.created_at.isoformat(),
                    "data": entry.data,
                }
                for entry in tool_entries
            ],
            "thought_logs": [
                {
                    "created_at": entry.created_at.isoformat(),
                    "data": entry.data,
                }
                for entry in thought_logs
            ],
            "tool_usage": [
                {
                    "tool_name": entry.tool_name,
                    "used_at": entry.used_at.isoformat(),
                    "metadata": json.loads(decrypt_text(entry.metadata_json))
                    if decrypt_text(entry.metadata_json)
                    else {},
                }
                for entry in tool_usage_entries
            ],
            "module_progress": [
                {
                    "module_id": entry.module_id,
                    "status": entry.status,
                    "progress_percent": entry.progress_percent,
                }
                for entry in progress_entries
            ],
        }
        app_capabilities = {
            "features": [
                "6-module CBT-based learning program",
                "BreathCheck Tool for paced breathing",
                "Thought Log tool for structured reflection",
            ]
        }
        if self._user_settings_service:
            settings = self._user_settings_service.get_settings()
            if not settings.ai_enabled:
                summary = self._fallback_summary(prompt_payload)
            else:
                summary = self._generate_ai_summary(app_capabilities, prompt_payload)
        else:
            summary = self._generate_ai_summary(app_capabilities, prompt_payload)
        with self._session_factory() as session:
            cached = self._insights_repo.create(
                session,
                summary_text=encrypt_text(summary),
                raw_data=encrypt_text(json.dumps(prompt_payload)),
            )
        logger.info("Generated insights")
        return _to_insight_entity(cached)

    def latest_cached(self) -> InsightEntity | None:
        with self._session_factory() as session:
            cached = self._insights_repo.latest(session)
        return _to_insight_entity(cached) if cached else None

    def module_snapshot(self) -> dict:
        module_entries = (
            self._module_data_service.list_module_data()
            if self._module_data_service
            else []
        )
        with self._session_factory() as session:
            progress_entries = self._progress_repo.list_all(session)
        payload = {entry.module_id: entry.data for entry in module_entries}
        payload["module_progress"] = [
            {
                "module_id": entry.module_id,
                "status": entry.status,
                "progress_percent": entry.progress_percent,
            }
            for entry in progress_entries
        ]
        return payload

    def _generate_ai_summary(self, app_capabilities: dict, prompt_payload: dict) -> str:
        prompt = (
            "Analyze the following anxiety program data. Provide professional, warm insights "
            "in 3 short paragraphs with clear, human tone. Avoid clinical diagnosis; focus on "
            "patterns, encouragement, and next steps. Recommend in-app activities when appropriate. "
            "Use these exact labels for each paragraph: Modules:, Tracking:, Tools:.\n"
            + json.dumps({"app_capabilities": app_capabilities, **prompt_payload})
        )
        if not self._ai_client.is_configured():
            return self._fallback_summary(prompt_payload)
        return self._ai_client.generate_insights(prompt)

    def _fallback_summary(self, prompt_payload: dict) -> str:
        progress = prompt_payload.get("module_progress", [])
        completed = sum(
            1
            for entry in progress
            if entry.get("status", "").upper() in {"COMPLETE", "COMPLETED"}
        )
        total = len(progress) if progress else 6
        tools = prompt_payload.get("tool_usage", [])
        tool_count = len(tools)
        thought_logs = prompt_payload.get("thought_logs", [])
        return (
            f"Modules: You have completed {completed} of {total} modules. Keep a steady pace and focus on the next unlocked module.\n"
            "Tracking: Your recent entries help establish patterns. Consistent engagement strengthens progress over time.\n"
            f"Tools: You have {tool_count} BreathCheck tool sessions and {len(thought_logs)} thought logs. "
            "Try a short breathing session when stress rises and capture one thought log this week."
        )

    def stream_thought_log_feedback(self, thought_log_data: dict):
        prompt = (
            "Provide brief, supportive feedback for this thought log entry. "
            "Use 3-5 sentences, avoid diagnosis, and suggest one realistic next step.\n"
            + json.dumps({"tool_name": "thought_log", "entry": thought_log_data})
        )
        if not self._ai_client.is_configured():
            yield (
                "You captured a clear thought pattern. "
                "Try one balanced alternative and test it in a small situation today."
            )
            return
        for token in self._ai_client.stream_thought_log_feedback(prompt):
            yield token
