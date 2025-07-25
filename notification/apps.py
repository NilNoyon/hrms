''' Django notifications apps file '''
# -*- coding: utf-8 -*-
from django.apps import AppConfig


class Config(AppConfig):
    name = "notification"

    def ready(self):
        super(Config, self).ready()
        # this is for backwards compability
        import notification.signals
        notification.notify = notification.signals.notify
