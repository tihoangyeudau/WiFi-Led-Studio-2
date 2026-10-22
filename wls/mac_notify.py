"""Native macOS notifications through UserNotifications."""
import logging
import subprocess
import threading
import uuid

_LOGGER = logging.getLogger(__name__)

_center = None
_authorized = None


def _get_center():
    global _center
    if _center is None:
        from Foundation import NSBundle
        from UserNotifications import UNUserNotificationCenter

        # UserNotifications aborts outside a real app bundle
        if NSBundle.mainBundle().bundleIdentifier() is None:
            raise RuntimeError("not running from an app bundle")
        _center = UNUserNotificationCenter.currentNotificationCenter()
    return _center


def _is_authorized(center):
    """Ask once for permission and wait for the answer."""
    global _authorized
    if _authorized is not None:
        return _authorized

    from UserNotifications import (
        UNAuthorizationOptionAlert,
        UNAuthorizationOptionSound,
    )

    answered = threading.Event()

    def done(granted, error):
        global _authorized
        _authorized = bool(granted)
        if error is not None:
            _LOGGER.debug(f"Notification authorization error: {error}")
        answered.set()

    center.requestAuthorizationWithOptions_completionHandler_(
        UNAuthorizationOptionAlert | UNAuthorizationOptionSound, done
    )
    # The user may be looking at the permission prompt
    if not answered.wait(60):
        return False
    return _authorized


def _notify_osascript(message, title):
    escape = lambda text: str(text).replace("\\", "\\\\").replace('"', '\\"')
    subprocess.check_call(
        [
            "osascript",
            "-e",
            f'display notification "{escape(message)}" '
            f'with title "{escape(title or "")}"',
        ]
    )


def notify(message, title=None):
    try:
        from UserNotifications import (
            UNMutableNotificationContent,
            UNNotificationRequest,
        )

        center = _get_center()
        if not _is_authorized(center):
            raise RuntimeError("notifications not allowed for this app")

        content = UNMutableNotificationContent.alloc().init()
        content.setTitle_(title or "")
        content.setBody_(message)
        request = UNNotificationRequest.requestWithIdentifier_content_trigger_(
            str(uuid.uuid4()), content, None
        )

        def added(error):
            if error is not None:
                _LOGGER.debug(f"Native notification failed: {error}")

        center.addNotificationRequest_withCompletionHandler_(request, added)
    except Exception as e:
        _LOGGER.debug(f"Falling back to osascript notification: {e}")
        _notify_osascript(message, title)
