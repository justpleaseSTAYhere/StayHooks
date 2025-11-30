# stayhere_webhooks

`STAYHERE_BASE_URL` is `http://localhost:3000` because StayHere is in Developement.

Python helper for managing StayHere room webhooks and delivering rich automation payloads. It mirrors the REST API exposed by `server/src/routes/webhooks.js` and adds conveniences for composing embeds, polls, and board drops from automation scripts, cron jobs, or CI tasks.

## Installation

This repository is not yet published to PyPI. Add the package to your virtual environment via an editable install:

```bash
pip install -e .
```

or, if you only want the webhook helper, point directly at the folder:

```bash
pip install -e ./stayhere_webhooks
```

The package requires Python 3.9+ (standard library only).

## Configuration

The client authenticates against your StayHere server using a room owner/admin JWT token. Provide the following environment variables or pass explicit values when constructing the client:

| Name | Purpose |
| --- | --- |
| `STAYHERE_BASE_URL` | Base URL for the StayHere server (default `http://localhost:3000`). |
| `STAYHERE_TOKEN` | API token for authenticated webhook management calls. |
| `STAYHERE_ROOM` | Default room ID for CLI helper `webhook.py`. |
| `STAYHERE_WEBHOOK` | Default webhook ID for CLI helper. |
| `STAYHERE_SECRET` | Shared secret used when invoking a webhook. |

## Quickstart

```python
from stayhere_webhooks import StayHereWebhookClient

client = StayHereWebhookClient(
    base_url="http://localhost:3000",
    token="<owner-token>",
    default_alias="Automation bot",
)

# Create a webhook and capture the secret once
bundle = client.create_webhook("ROOM123", label="Deploy bot", permissions=["message", "embed"])
print("Invoke URL:", bundle.invoke_url)
print("Secret:", bundle.secret)

# Send a rich embed update
result = client.send_embed(
    room_id="ROOM123",
    webhook_id=bundle.webhook.id,
    secret=bundle.secret,
    title="Release 1.2 shipped",
    description="Primary API rollout complete",
    notes=["Latency < 180ms", "Docs refreshed"],
    color="#22c55e",
    text="Status: SUCCESS",
)
print(result)
```

## API Highlights

| Method | Description |
| --- | --- |
| `list_webhooks(room_id)` | Fetch metadata for every webhook in a room. |
| `create_webhook(room_id, label, permissions)` | Provision a new webhook and return its secret. |
| `update_webhook(room_id, webhook_id, ...)` | Rename, pause, or change permissions. |
| `rotate_secret(room_id, webhook_id)` | Generate a fresh secret without deleting the webhook. |
| `delete_webhook(room_id, webhook_id)` | Remove webhook credentials entirely. |
| `get_permitted_actions(room_id)` | Discover supported actions and per-room limits. |
| `send_message(...)` | Post plain-text chat messages (with alias + attachments via `extra`). |
| `send_embed(...)` | Deliver rich cards with colors, image, footer, and bullet notes. |
| `send_poll(...)` | Launch polls with up to eight options and optional end timers. |
| `send_image(...)` | Place hosted images onto the collaborative board with sizing hints. |
| `invoke_webhook(...)` | Low-level helper when you already have the invoke URL. |

## Examples

Check the `examples/` directory for tiny, self-contained Python scripts that demonstrate each action (`send_message.py`, `send_embed.py`, `send_poll.py`, `send_image.py`). Each script requires you to fill in the base URL, room ID, webhook ID, and secret at the top, then run `python examples/<script>.py` to trigger the corresponding webhook.

## Error Handling

- All SDK errors inherit from `StayHereError`.
- HTTP 401/403 responses raise `StayHereAuthError`.
- Other non-2xx responses raise `StayHereHTTPError` and include the parsed JSON body (if any).
- Invalid arguments trigger `StayHereValidationError` before a network request is attempted.
- Network interruptions bubble up as `StayHereError` with the underlying reason.

Wrap calls in `try/except StayHereError` to gracefully surface actionable diagnostics.
