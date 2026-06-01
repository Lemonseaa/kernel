"""Built-in notification channels."""

from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from typing import Callable
from urllib import request

from kernel.notification.base import NotificationChannel, NotificationDelivery, NotificationMessage


class ConsoleNotificationChannel(NotificationChannel):
    """Print notifications to stdout."""

    name = "console"

    def send(self, message: NotificationMessage) -> NotificationDelivery:
        """Print one message."""

        print(f"[{message.priority.upper()}] {message.title}\n{message.body}")
        return NotificationDelivery(channel=self.name, success=True, message_id=message.id)


class WebhookNotificationChannel(NotificationChannel):
    """Send notifications to a generic JSON webhook."""

    name = "webhook"

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        transport: Callable[[str, dict[str, object], dict[str, str]], object] | None = None,
        payload_builder: Callable[[NotificationMessage], dict[str, object]] | None = None,
    ) -> None:
        """Create a webhook channel."""

        self.url = url
        self.headers = headers or {}
        self.transport = transport or self._default_transport
        self.payload_builder = payload_builder

    def send(self, message: NotificationMessage) -> NotificationDelivery:
        """POST message JSON to the webhook."""

        try:
            payload = self.payload_builder(message) if self.payload_builder else message.to_dict()
            self.transport(self.url, payload, self.headers)
            return NotificationDelivery(channel=self.name, success=True, message_id=message.id)
        except Exception as exc:
            return NotificationDelivery(channel=self.name, success=False, message_id=message.id, error=str(exc))

    def _default_transport(self, url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
        """Send the webhook with standard library HTTP."""

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        merged_headers = {"Content-Type": "application/json", **headers}
        req = request.Request(url, data=body, headers=merged_headers, method="POST")
        with request.urlopen(req, timeout=10) as response:  # noqa: S310 - caller controls trusted webhook URL.
            return {"status": response.status}


class EmailNotificationChannel(NotificationChannel):
    """Send notifications through SMTP."""

    name = "email"

    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        recipients: list[str],
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        smtp_factory: Callable[[str, int], smtplib.SMTP] | None = None,
    ) -> None:
        """Create an SMTP notification channel."""

        self.host = host
        self.port = port
        self.sender = sender
        self.recipients = recipients
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.smtp_factory = smtp_factory or smtplib.SMTP

    def send(self, message: NotificationMessage) -> NotificationDelivery:
        """Send one email."""

        email = EmailMessage()
        email["From"] = self.sender
        email["To"] = ", ".join(self.recipients)
        email["Subject"] = message.title
        email.set_content(message.body)
        try:
            with self.smtp_factory(self.host, self.port) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(email)
            return NotificationDelivery(channel=self.name, success=True, message_id=message.id)
        except Exception as exc:
            return NotificationDelivery(channel=self.name, success=False, message_id=message.id, error=str(exc))
