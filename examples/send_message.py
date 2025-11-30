"""StayHere message example using stayhooks client.

Fill in the placeholders and run: python examples/send_message.py
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
	client = StayHereWebhookClient(base_url=BASE_URL, default_alias="Automation bot")
	result = client.send_message(
		room_id=ROOM_ID,
		webhook_id=WEBHOOK_ID,
		secret=WEBHOOK_SECRET,
		text="Deployment started 🚀",
	)
	print(result)


if __name__ == "__main__":
	main()
