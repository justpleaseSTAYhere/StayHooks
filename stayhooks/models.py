"""Dataclasses that mirror StayHere webhook API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Webhook:
    id: str
    label: str
    permissions: List[str]
    paused: bool = False
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    last_used_at: Optional[str] = None
    secret_preview: Optional[str] = None
    invoke_url: Optional[str] = None
    example_curl: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        return cls(
            id=data.get("id", ""),
            label=data.get("label", ""),
            permissions=list(data.get("permissions") or []),
            paused=bool(data.get("paused", False)),
            created_at=data.get("createdAt"),
            created_by=data.get("createdBy"),
            last_used_at=data.get("lastUsedAt"),
            secret_preview=data.get("secretPreview"),
            invoke_url=data.get("invokeUrl"),
            example_curl=data.get("exampleCurl"),
        )


@dataclass
class WebhookSecretBundle:
    webhook: Webhook
    secret: str
    invoke_url: Optional[str] = None
    example_curl: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookSecretBundle":
        return cls(
            webhook=Webhook.from_dict(data.get("webhook", {})),
            secret=data.get("secret", ""),
            invoke_url=data.get("invokeUrl") or data.get("webhook", {}).get("invokeUrl"),
            example_curl=data.get("exampleCurl") or data.get("webhook", {}).get("exampleCurl"),
        )


@dataclass
class InvokeResult:
    ok: bool
    kind: Optional[str] = None
    message_id: Optional[str] = None
    poll_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvokeResult":
        return cls(
            ok=bool(data.get("ok", False)),
            kind=data.get("kind"),
            message_id=data.get("messageId"),
            poll_id=data.get("pollId"),
            extra={k: v for k, v in data.items() if k not in {"ok", "kind", "messageId", "pollId"}},
        )


@dataclass
class PermittedActions:
    actions: List[str]
    limit: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermittedActions":
        return cls(actions=list(data.get("actions") or []), limit=int(data.get("limit") or 0))