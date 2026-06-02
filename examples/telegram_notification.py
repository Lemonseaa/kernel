"""Telegram notification webhook example."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opc_os.notification import NotificationManager, NotificationMessage, WebhookNotificationChannel


def main() -> None:
    """Send a Telegram message through the Bot API webhook."""

    token = os.getenv("TELEGRAM_BOT_TOKEN", "replace-with-token")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "replace-with-chat-id")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    channel = WebhookNotificationChannel(
        url,
        payload_builder=lambda message: {
            "chat_id": chat_id,
            "text": f"{message.title}\n\n{message.body}",
        },
    )
    manager = NotificationManager([channel])
    message = NotificationMessage(
        title="OPCOS通知",
        body="有任务需要人工处理。",
        type="approval_required",
        priority="high",
        data={"chat_id": chat_id},
    )
    print(manager.notify(message))


if __name__ == "__main__":
    main()
