"""High-level Python client for the StayHere webhook APIs."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib import error, parse, request

from .errors import (
    StayHereAuthError,
    StayHereError,
    StayHereHTTPError,
    StayHereValidationError,
    StayHereWebhookInvokeError,
)
from .models import InvokeResult, PermittedActions, Webhook, WebhookSecretBundle

WEBHOOK_SECRET_HEADER = "x-stay-webhook-secret"
DEFAULT_PERMISSIONS = ("message", "embed", "poll", "image")


class StayHereWebhookClient:
    """Manage StayHere webhooks and send payloads programmatically."""

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        *,
        token: Optional[str] = None,
        api_prefix: str = "/api",
        timeout: float = 10.0,
        user_agent: str = "stayhere-webhooks/0.1",
        default_alias: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.api_prefix = self._normalize_api_prefix(api_prefix)
        self.timeout = timeout
        self.user_agent = user_agent
        self.default_alias = default_alias

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def list_webhooks(self, room_id: str) -> Dict[str, Any]:
        """Return metadata + dataclass objects for every webhook in a room."""

        data = self._request("GET", f"/webhooks/{self._encode(room_id)}")
        hooks = [Webhook.from_dict(item) for item in data.get("webhooks", [])]
        return {
            "room_id": data.get("roomId"),
            "limit": data.get("limit"),
            "webhooks": hooks,
        }

    def create_webhook(
        self,
        room_id: str,
        *,
        label: str,
        permissions: Optional[Sequence[str]] = None,
    ) -> WebhookSecretBundle:
        payload = {
            "label": label,
            "permissions": self._normalize_permissions(permissions),
        }
        data = self._request("POST", f"/webhooks/{self._encode(room_id)}", body=payload)
        return WebhookSecretBundle.from_dict(data)

    def update_webhook(
        self,
        room_id: str,
        webhook_id: str,
        *,
        label: Optional[str] = None,
        permissions: Optional[Sequence[str]] = None,
        paused: Optional[bool] = None,
    ) -> Webhook:
        payload: Dict[str, Any] = {}
        if label is not None:
            payload["label"] = label
        if permissions is not None:
            payload["permissions"] = self._normalize_permissions(permissions)
        if paused is not None:
            payload["paused"] = bool(paused)
        data = self._request(
            "PATCH",
            f"/webhooks/{self._encode(room_id)}/{self._encode(webhook_id)}",
            body=payload or None,
        )
        return Webhook.from_dict(data.get("webhook", data))

    def rotate_secret(self, room_id: str, webhook_id: str) -> WebhookSecretBundle:
        data = self._request(
            "POST",
            f"/webhooks/{self._encode(room_id)}/{self._encode(webhook_id)}/rotate",
        )
        return WebhookSecretBundle.from_dict(data)

    def delete_webhook(self, room_id: str, webhook_id: str) -> bool:
        data = self._request(
            "DELETE",
            f"/webhooks/{self._encode(room_id)}/{self._encode(webhook_id)}",
        )
        return bool(data.get("ok", True))

    def get_permitted_actions(self, room_id: str) -> PermittedActions:
        data = self._request(
            "GET",
            f"/webhooks/{self._encode(room_id)}/meta/permitted-actions",
        )
        return PermittedActions.from_dict(data)

    # ------------------------------------------------------------------
    # Invocation helpers
    # ------------------------------------------------------------------
    def invoke_webhook(
        self,
        *,
        secret: str,
        action: str,
        payload: Dict[str, Any],
        room_id: Optional[str] = None,
        webhook_id: Optional[str] = None,
        invoke_url: Optional[str] = None,
    ) -> InvokeResult:
        if not invoke_url:
            if not room_id or not webhook_id:
                raise StayHereValidationError(
                    "room_id and webhook_id are required when invoke_url is missing"
                )
            path = f"/webhooks/{self._encode(room_id)}/{self._encode(webhook_id)}/invoke"
            full_url = self._build_url(path)
        else:
            full_url = invoke_url
        body = {"action": action, "payload": payload}
        headers = {WEBHOOK_SECRET_HEADER: secret}
        data = self._request(
            "POST",
            full_url=full_url,
            body=body,
            headers=headers,
            auth=False,
        )
        return InvokeResult.from_dict(data)

    def send_message(
        self,
        room_id: str,
        webhook_id: str,
        *,
        secret: str,
        text: str,
        alias: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> InvokeResult:
        text_value = (text or "").strip()
        if not text_value:
            raise StayHereValidationError("Message text must be provided")
        payload: Dict[str, Any] = {"text": text_value}
        alias_value = alias or self.default_alias
        if alias_value:
            payload["alias"] = alias_value
        if extra:
            payload.update(extra)
        return self.invoke_webhook(
            room_id=room_id,
            webhook_id=webhook_id,
            secret=secret,
            action="message",
            payload=payload,
        )

    def send_embed(
        self,
        room_id: str,
        webhook_id: str,
        *,
        secret: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        url: Optional[str] = None,
        image: Optional[str] = None,
        footer: Optional[str] = None,
        text: Optional[str] = None,
        alias: Optional[str] = None,
        notes: Optional[Iterable[str]] = None,
        extra_embed_fields: Optional[Dict[str, Any]] = None,
    ) -> InvokeResult:
        embed: Dict[str, Any] = {}
        if title:
            embed["title"] = title
        if description:
            embed["description"] = description
        if color:
            embed["color"] = color
        if url:
            embed["url"] = url
        if image:
            embed["image"] = image
        if footer:
            embed["footer"] = footer
        if notes:
            extra_lines = [note.strip() for note in notes if note and note.strip()]
            if extra_lines:
                current_desc = embed.get("description", "").strip()
                bullet_block = "\n".join(f"• {line}" for line in extra_lines)
                embed["description"] = (
                    f"{current_desc}\n\n{bullet_block}" if current_desc else bullet_block
                )
        if extra_embed_fields:
            embed.update(extra_embed_fields)
        if not embed:
            raise StayHereValidationError("Embed payload must include at least one field")
        payload: Dict[str, Any] = {"embed": embed}
        if text:
            payload["text"] = text
        alias_value = alias or self.default_alias
        if alias_value:
            payload["alias"] = alias_value
        return self.invoke_webhook(
            room_id=room_id,
            webhook_id=webhook_id,
            secret=secret,
            action="embed",
            payload=payload,
        )

    def send_poll(
        self,
        room_id: str,
        webhook_id: str,
        *,
        secret: str,
        question: str,
        options: Sequence[str],
        multiple_choice: bool = False,
        ends_in_minutes: Optional[int] = None,
    ) -> InvokeResult:
        clean_opts = [opt.strip() for opt in options if opt and opt.strip()]
        if len(clean_opts) < 2:
            raise StayHereValidationError("A poll must include at least two options")
        question_value = (question or "").strip()
        if not question_value:
            raise StayHereValidationError("Poll question cannot be empty")
        payload: Dict[str, Any] = {
            "question": question_value,
            "options": clean_opts[:8],
            "multipleChoice": bool(multiple_choice),
        }
        if ends_in_minutes:
            payload["endsInMinutes"] = int(ends_in_minutes)
        return self.invoke_webhook(
            room_id=room_id,
            webhook_id=webhook_id,
            secret=secret,
            action="poll",
            payload=payload,
        )

    def send_image(
        self,
        room_id: str,
        webhook_id: str,
        *,
        secret: str,
        url: str,
        size: Optional[Tuple[int, int]] = None,
        position: Optional[Tuple[int, int]] = None,
    ) -> InvokeResult:
        img_url = (url or "").strip()
        if not img_url.startswith("http"):
            raise StayHereValidationError("Image URL must be an http/https URL")
        payload: Dict[str, Any] = {"url": img_url}
        if size:
            payload["w"], payload["h"] = map(int, size)
        if position:
            payload["x"], payload["y"] = map(int, position)
        return self.invoke_webhook(
            room_id=room_id,
            webhook_id=webhook_id,
            secret=secret,
            action="image",
            payload=payload,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: Optional[str] = None,
        *,
        full_url: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: bool = True,
    ) -> Dict[str, Any]:
        url = full_url or self._build_url(path or "/")
        data = json.dumps(body, separators=(",", ":")).encode("utf-8") if body else None
        req_headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if data:
            req_headers["Content-Type"] = "application/json"
        if auth:
            if not self.token:
                raise StayHereAuthError(401, "Missing API token for this request")
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)
        req = request.Request(url, data=data, headers=req_headers, method=method.upper())
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            parsed = self._attempt_json(payload)
            err_cls = StayHereAuthError if exc.code in (401, 403) else StayHereHTTPError
            raise err_cls(exc.code, parsed.get("error") or payload or str(exc), payload=parsed)
        except error.URLError as exc:
            raise StayHereError(f"Failed to reach StayHere server: {exc.reason}")
        except Exception as exc:  # pragma: no cover - defensive logging
            raise StayHereError(str(exc))
        return self._safe_json(raw)

    def _safe_json(self, raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise StayHereWebhookInvokeError("Server response was not valid JSON", payload=raw)

    def _attempt_json(self, raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _normalize_permissions(self, perms: Optional[Sequence[str]]) -> List[str]:
        if perms is None:
            return list(DEFAULT_PERMISSIONS)
        cleaned = []
        for perm in perms:
            if not perm:
                continue
            key = perm.strip().lower()
            if key in DEFAULT_PERMISSIONS and key not in cleaned:
                cleaned.append(key)
        return cleaned or list(DEFAULT_PERMISSIONS)

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        prefix = self.api_prefix
        return f"{self.base_url}{prefix}{path}"

    def _encode(self, value: str) -> str:
        return parse.quote(str(value), safe="")

    @staticmethod
    def _normalize_api_prefix(prefix: str) -> str:
        if not prefix:
            return ""
        trimmed = prefix.strip()
        if not trimmed:
            return ""
        return "/" + trimmed.strip("/")
