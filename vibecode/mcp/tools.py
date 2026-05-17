from __future__ import annotations

import json
from typing import Any

from vibecode.core.memory_service import VibeCodeService


class MCPTools:
    def __init__(self) -> None:
        self.service = VibeCodeService()

    def search_memory(self, query: str, project_path: str | None = None, language: str | None = None, max_results: int = 10) -> str:
        result = self.service.search_memory(
            query=query,
            project_path=project_path,
            language=language,
            max_results=max_results,
        )
        return json.dumps(result, indent=2)

    def inject_context(self, query: str, project_path: str | None = None, agent_profile: str = "generic-agent", max_context_tokens: int | None = None) -> str:
        result = self.service.inject_context(
            query=query,
            project_path=project_path,
            agent_profile=agent_profile,
            max_context_tokens=max_context_tokens,
        )
        return json.dumps(result, indent=2)

    def capture_success(self, project_path: str, name: str, intent_description: str, **kwargs: Any) -> str:
        result = self.service.capture_success(
            project_path=project_path,
            name=name,
            intent_description=intent_description,
            **kwargs,
        )
        return json.dumps(result, indent=2)

    def capture_failure(self, project_path: str, task_intent: str, bad_suggestion: str, failure_reason: str, prevention_rule: str, **kwargs: Any) -> str:
        result = self.service.capture_failure(
            project_path=project_path,
            task_intent=task_intent,
            bad_suggestion=bad_suggestion,
            failure_reason=failure_reason,
            prevention_rule=prevention_rule,
            **kwargs,
        )
        return json.dumps(result, indent=2)

    def add_project_rule(self, project_path: str, rule_text: str, rule_type: str, **kwargs: Any) -> str:
        result = self.service.add_project_rule(
            project_path=project_path,
            rule_text=rule_text,
            rule_type=rule_type,
            **kwargs,
        )
        return json.dumps(result, indent=2)

    def token_report(self, project_path: str | None = None, days: int = 30) -> str:
        result = self.service.get_token_report(project_path=project_path, days=days)
        return json.dumps(result, indent=2)

    def health_check(self) -> str:
        result = self.service.health_check()
        return json.dumps(result, indent=2)
