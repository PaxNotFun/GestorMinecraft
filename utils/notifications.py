from plyer import notification


def send_notification(title, message, app_name="GetMineHub"):
    """Envía una notificación de escritorio."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            timeout=10
        )
    except Exception:
        pass


class ToastNotification:
    pass