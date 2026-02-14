from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Iterator, Optional

from anxiety_app.core.security import get_api_key

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(
        self,
        service_name: str,
        api_key_env: str | None = None,
        model_name: str = "gpt-5.2",
    ) -> None:
        self._service_name = service_name
        self._api_key_env = api_key_env or ""
        self._model_name = model_name

    @property
    def service_name(self) -> str:
        return self._service_name

    def _resolve_api_key(self) -> Optional[str]:
        if self._api_key_env:
            return self._api_key_env
        return get_api_key(self._service_name)

    def is_configured(self) -> bool:
        return bool(self._resolve_api_key())

    def validate_key(self) -> tuple[bool, str]:
        api_key = self._resolve_api_key()
        if not api_key:
            return False, "No API key found."
        try:
            request = urllib.request.Request(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=6) as response:
                if response.status == 200:
                    return True, "API key is valid."
                return False, f"API check failed: HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            return False, f"API check failed: HTTP {exc.code}"
        except Exception as exc:
            return False, f"API check failed: {exc}"

    def generate_insights(self, prompt: str) -> str:
        api_key = self._resolve_api_key()
        if not api_key:
            logger.info("No API key configured; returning stubbed insights")
            return (
                "Insights are currently using a stubbed response. "
                "Add an API key to enable richer analysis."
            )
        payload = {
            "model": self._model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a supportive, professional mental health assistant. "
                        "Avoid diagnosis. Provide actionable, gentle insights."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
            message = body["choices"][0]["message"]["content"].strip()
            logger.info("Generated insights via AI backend using %s", self._model_name)
            return message
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            logger.error("AI request failed: HTTP %s %s", exc.code, error_body)
            raise RuntimeError("AI request failed") from exc
        except Exception as exc:
            logger.error("AI request failed: %s", exc)
            raise RuntimeError("AI request failed") from exc

    def stream_thought_log_feedback(self, prompt: str) -> Iterator[str]:
        api_key = self._resolve_api_key()
        if not api_key:
            yield (
                "Focus on one realistic next step and test a balanced thought. "
                "Repeat this skill once today."
            )
            return

        payload = {
            "model": self._model_name,
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a supportive, professional mental health assistant. "
                        "Avoid diagnosis. Provide actionable, gentle insights."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    payload_str = line[5:].strip()
                    if payload_str == "[DONE]":
                        break
                    if not payload_str:
                        continue
                    try:
                        chunk = json.loads(payload_str)
                    except Exception:
                        continue
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    token = delta.get("content")
                    if token:
                        yield token
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            logger.error("Streaming AI request failed: HTTP %s %s", exc.code, error_body)
            raise RuntimeError("Streaming AI request failed") from exc
        except Exception as exc:
            logger.error("Streaming AI request failed: %s", exc)
            raise RuntimeError("Streaming AI request failed") from exc
