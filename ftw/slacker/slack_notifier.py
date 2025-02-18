from ftw.slacker.interfaces import ISlackNotifier
from threading import Thread
from zope.component import getUtility
from zope.interface import implements
import os
import requests


def notify_slack(*args, **kwargs):
    """This is the main api function to perform a slack notification

    Always use this function to do slack notifications.

    See the readme.rst to find out how to use it.
    """
    slacker = getUtility(ISlackNotifier)
    return slacker.notify(*args, **kwargs)


# Use this string in your environment variables to deactivamete
# notification.
NOTIFICATION_DEACTIVATION_VALUE = 'deactivate'

# Possible environment variables
STANDARD_SLACK_WEBHOOK = 'STANDARD_SLACK_WEBHOOK'
DEACTIVATE_SLACK_NOTIFICATION = 'DEACTIVATE_SLACK_NOTIFICATION'


class SlackNotifier(object):
    """The default slack notifier utility posts a message into slack through
    a webhook.
    """
    implements(ISlackNotifier)

    # Name of the request thread
    THREAD_NAME = 'SlackNotifier-Thread'

    def notify(self, webhook_url=None, timeout=2, verify=True, **payload):
        """Performs the slack notification
        """
        if self._is_notification_globally_deactivated():
            return

        webhook_url = self._choose_webhook_url(webhook_url)
        if self._is_notification_deactivated(webhook_url):
            return

        thread = Thread(target=self._do_request,
                        name=self.THREAD_NAME,
                        args=(webhook_url, timeout, verify),
                        kwargs=payload)

        thread.start()
        return thread

    def _do_request(self, webhook_url=None, timeout=2, verify=True, **payload):
        """Actually performs the request.
        """
        requests.post(webhook_url,
                      timeout=timeout,
                      verify=verify,
                      json=payload,).raise_for_status()

    def _choose_webhook_url(self, webhook_url):
        """Chooses the proper webhook_url. It returns the current webhook_url or a
        fallback value from an environment variable.
        """
        return webhook_url or os.environ.get(STANDARD_SLACK_WEBHOOK)

    def _is_notification_deactivated(self, webhook_url):
        """Checks if the notification is deactivated based on the current webhook_url.
        """
        if not webhook_url:
            return True
        return webhook_url.lower() == NOTIFICATION_DEACTIVATION_VALUE

    def _is_notification_globally_deactivated(self):
        """Checks if the notification is globally deactivated through
        an environment variable.
        """
        value = os.environ.get(DEACTIVATE_SLACK_NOTIFICATION)
        if not value:
            return False

        return value.lower() == NOTIFICATION_DEACTIVATION_VALUE
