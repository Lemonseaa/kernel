"""Notification manager."""

from __future__ import annotations

from opc_os.notification.base import NotificationChannel, NotificationDelivery, NotificationMessage


class NotificationManager:
    """Fan out notifications to registered channels."""

    def __init__(self, channels: list[NotificationChannel] | None = None) -> None:
        """Create a notification manager."""

        self.channels: dict[str, NotificationChannel] = {}
        self.history: list[NotificationMessage] = []
        self.deliveries: list[NotificationDelivery] = []
        for channel in channels or []:
            self.register(channel)

    def register(self, channel: NotificationChannel) -> None:
        """Register or replace a channel."""

        self.channels[channel.name] = channel

    def unregister(self, name: str) -> None:
        """Remove a registered channel."""

        self.channels.pop(name, None)

    def notify(
        self,
        message: NotificationMessage,
        channel_names: list[str] | None = None,
    ) -> list[NotificationDelivery]:
        """Send a message through selected channels."""

        targets = self._selected_channels(channel_names)
        deliveries: list[NotificationDelivery] = []
        for channel in targets:
            try:
                delivery = channel.send(message)
            except Exception as exc:
                delivery = NotificationDelivery(channel=channel.name, success=False, message_id=message.id, error=str(exc))
            deliveries.append(delivery)
        self.history.append(message)
        self.deliveries.extend(deliveries)
        return deliveries

    async def anotify(
        self,
        message: NotificationMessage,
        channel_names: list[str] | None = None,
    ) -> list[NotificationDelivery]:
        """Async-compatible notification entrypoint."""

        return self.notify(message, channel_names=channel_names)

    def notify_approval_required(self, task: object, reason: str = "") -> list[NotificationDelivery]:
        """Notify humans that a task is waiting for approval."""

        task_id = str(getattr(task, "id", ""))
        description = str(getattr(task, "name", "task"))
        return self.notify(
            NotificationMessage(
                title=f"需要审批: {description[:50]}",
                body=f"任务ID: {task_id}\n原因: {reason}",
                type="approval_required",
                priority="high",
                data={"task_id": task_id},
            )
        )

    def notify_task_complete(self, task: object) -> list[NotificationDelivery]:
        """Notify humans that a task has completed."""

        task_id = str(getattr(task, "id", ""))
        description = str(getattr(task, "name", "task"))
        state = getattr(getattr(task, "state", ""), "value", getattr(task, "state", ""))
        return self.notify(
            NotificationMessage(
                title=f"任务完成: {description[:50]}",
                body=f"任务ID: {task_id}\n状态: {state}",
                type="task_completed",
                data={"task_id": task_id, "state": state},
            )
        )

    def notify_alert(self, message: str, data: dict[str, object] | None = None) -> list[NotificationDelivery]:
        """Send a high-priority alert."""

        return self.notify(
            NotificationMessage(
                title="系统告警",
                body=message,
                type="alert",
                priority="high",
                data=data or {},
            )
        )

    def _selected_channels(self, channel_names: list[str] | None) -> list[NotificationChannel]:
        """Resolve notification target channels."""

        if channel_names is None:
            return list(self.channels.values())
        return [self.channels[name] for name in channel_names if name in self.channels]
