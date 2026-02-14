from __future__ import annotations

import json
from typing import Iterator

from anxiety_app.services.ai_client import AIClient


class ToolFeedbackService:
    def __init__(self, ai_client: AIClient) -> None:
        self._ai_client = ai_client

    def is_configured(self) -> bool:
        return self._ai_client.is_configured()

    def generate_feedback(self, tool_name: str, payload: dict) -> str:
        if not self._ai_client.is_configured():
            return self._fallback_feedback(tool_name, payload)
        prompt = (
            "Provide brief, supportive feedback for the following CBT tool entry. "
            "Use 3-5 sentences, avoid diagnosis, and suggest a helpful next step.\n"
            + json.dumps({"tool_name": tool_name, "entry": payload})
        )
        text = self._ai_client.generate_insights(prompt)
        if "stubbed response" in text.lower():
            return self._fallback_feedback(tool_name, payload)
        return text

    def stream_feedback(self, tool_name: str, payload: dict) -> Iterator[str]:
        if not self._ai_client.is_configured():
            yield self._fallback_feedback(tool_name, payload)
            return
        prompt = (
            "Provide brief, supportive feedback for the following CBT tool entry. "
            "Use 3-5 sentences, avoid diagnosis, and suggest a helpful next step.\n"
            + json.dumps({"tool_name": tool_name, "entry": payload})
        )
        try:
            yielded = False
            for token in self._ai_client.stream_thought_log_feedback(prompt):
                yielded = True
                yield token
            if not yielded:
                yield self._fallback_feedback(tool_name, payload)
        except Exception:
            yield self._fallback_feedback(tool_name, payload)

    def fallback_feedback(self, tool_name: str, payload: dict) -> str:
        return self._fallback_feedback(tool_name, payload)

    def _fallback_feedback(self, tool_name: str, payload: dict) -> str:
        if tool_name == "thought_log":
            intensity = int(payload.get("emotion_intensity", 0) or 0)
            rerate = int(payload.get("emotion_rerate", intensity) or intensity)
            shift = intensity - rerate
            direction = (
                "your intensity lowered after reframing"
                if shift > 0
                else "your intensity stayed the same"
            )
            return (
                "You captured a clear situation and thought pattern. "
                f"After re-rating, {direction}. "
                "Keep the alternative thought practical and testable today. "
                "Small repetitions make this skill stronger."
            )
        return (
            "You completed a useful coping step. "
            "Notice what changed in your body and thinking. "
            "Repeat this once more today if anxiety rises."
        )
