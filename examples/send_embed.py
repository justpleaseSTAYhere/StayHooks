"""
StayHere embed webhook example.

Fill in the placeholders and run: python examples/send_embed.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stayhooks import StayHereWebhookClient  # type: ignore

BASE_URL = "http://localhost:3000"
ROOM_ID = "your-room-id"
WEBHOOK_ID = "webhook-id"
WEBHOOK_SECRET = "whk_secret_from_dashboard"


def main() -> None:
	client = StayHereWebhookClient(base_url=BASE_URL, default_alias="Automation bot")
	notes = [
		"Latency < 200ms",
		"Docs refreshed",
		f"Timestamp: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}",
	]
	result = client.send_embed(
		room_id=ROOM_ID,
		webhook_id=WEBHOOK_ID,
		secret=WEBHOOK_SECRET,
		title="Release 1.2 shipped",
		description="Production push completed",
		color="#22c55e",
		footer="Sent via stayhooks example",
		notes=notes,
		text="Status · SUCCESS",
	)
	print(result)


if __name__ == "__main__":
	main()
