"""
StayHere poll example using stayhooks client.

Fill in the placeholders and run: python examples/send_poll.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stayhooks import StayHereWebhookClient  # type: ignore

BASE_URL = "http://localhost:3000"
ROOM_ID = "your-room-id"
WEBHOOK_ID = "webhook-id"
WEBHOOK_SECRET = "whk_secret_from_dashboard"


def main() -> None:
	client = StayHereWebhookClient(base_url=BASE_URL)
	result = client.send_poll(
		room_id=ROOM_ID,
		webhook_id=WEBHOOK_ID,
		secret=WEBHOOK_SECRET,
		question="Which feature ships next?",
		options=["Docs revamp", "AI assistant", "Canvas refresh"],
		multiple_choice=False,
		ends_in_minutes=30,
	)
	print(result)


if __name__ == "__main__":
	main()
