# from general.models import Users
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from notification import settings as notification_settings
from django.conf import settings
from notification.signals import notify
from notification.utils import id2slug
from django.contrib.contenttypes.fields import GenericForeignKey


EXTRA_DATA = notification_settings.get_config()['USE_JSONFIELD']
EXTRA_DATA = getattr(settings, 'USE_JSONFIELD', False)


def is_soft_delete():
    return notification_settings.get_config()['SOFT_DELETE']


def assert_soft_delete():
    if not is_soft_delete():
        # msg = """To use 'deleted' field, please set 'SOFT_DELETE'=True in settings.
        # Otherwise NotificationQuerySet.unread and NotificationQuerySet.read do NOT filter by 'deleted' field.
        # """
        msg = 'REVERTME'
        raise ImproperlyConfigured(msg)


class NotificationQuerySet(models.query.QuerySet):
    ''' Notification QuerySet '''
    def unsent(self):
        return self.filter(emailed=False)

    def sent(self):
        return self.filter(emailed=True)

    def unread(self, include_deleted=False):
        """Return only unread items in the current queryset"""
        if is_soft_delete() and not include_deleted:
            return self.filter(unread=True, deleted=False)

        # When SOFT_DELETE=False, developers are supposed NOT to touch 'deleted' field.
        # In this case, to improve query performance, don't filter by 'deleted' field
        return self.filter(unread=True)

    def read(self, include_deleted=False):
        """Return only read items in the current queryset"""
        if is_soft_delete() and not include_deleted:
            return self.filter(unread=False, deleted=False)

        # When SOFT_DELETE=False, developers are supposed NOT to touch 'deleted' field.
        # In this case, to improve query performance, don't filter by 'deleted' field
        return self.filter(unread=False)

    def mark_all_as_read(self, recipient=None):
        """Mark as read any unread messages in the current queryset.

        Optionally, filter these by recipient first.
        """
        # We want to filter out read ones, as later we will store
        # the time they were marked as read.
        qset = self.unread(True)
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(unread=False)

    def mark_all_as_unread(self, recipient=None):
        """Mark as unread any read messages in the current queryset.

        Optionally, filter these by recipient first.
        """
        qset = self.read(True)

        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(unread=True)

    def deleted(self):
        """Return only deleted items in the current queryset"""
        assert_soft_delete()
        return self.filter(deleted=True)

    def active(self):
        """Return only active(un-deleted) items in the current queryset"""
        assert_soft_delete()
        return self.filter(deleted=False)

    def mark_all_as_deleted(self, recipient=None):
        """Mark current queryset as deleted.
        Optionally, filter by recipient first.
        """
        assert_soft_delete()
        qset = self.active()
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(deleted=True)

    def mark_all_as_active(self, recipient=None):
        """Mark current queryset as active(un-deleted).
        Optionally, filter by recipient first.
        """
        assert_soft_delete()
        qset = self.deleted()
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(deleted=False)

    def mark_as_unsent(self, recipient=None):
        qset = self.sent()
        if recipient:
            qset = qset.filter(recipient=recipient)
        return qset.update(emailed=False)

    def mark_as_sent(self, recipient=None):
        qset = self.unsent()
        if recipient:
            qset = qset.filter(recipient=recipient)
        return qset.update(emailed=True)


class Notification(models.Model):
    level_types = (
        ('success', 'Success'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    )
    level = models.CharField(max_length=20, choices=level_types, default='info')

    recipient = models.ForeignKey(
        'general.Users',
        blank=False,
        related_name='notification',
        on_delete=models.CASCADE
    )
    unread = models.BooleanField(default=True, blank=False, db_index=True)

    actor_content_type = models.ForeignKey(ContentType, related_name='notify_actor', on_delete=models.CASCADE)
    actor_object_id = models.CharField(max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    target_content_type = models.ForeignKey(
        ContentType,
        related_name='notify_target',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action_object_content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                                   related_name='notify_action_object', on_delete=models.CASCADE)
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    timestamp   = models.DateTimeField(default=timezone.now, db_index=True)

    public      = models.BooleanField(default=True, db_index=True)
    deleted     = models.BooleanField(default=False, db_index=True)
    emailed     = models.BooleanField(default=False, db_index=True)
    action_url  = models.CharField(max_length=255, blank=True, null=True)
    model       = models.CharField(max_length=50, blank=True, null=True)

    objects     = NotificationQuerySet.as_manager()
    

    class Meta:
        db_table    = 'system_notifications'
        ordering    = ('-timestamp',)
        app_label   = 'notification'
        # speed up notification count query
        # index_together = ('recipient', 'unread')
        # index_together = [
        #     ['recipient', 'unread'],
        # ]

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return u'%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago' % ctx
            return u'%(actor)s %(verb)s %(target)s %(timesince)s ago' % ctx
        if self.action_object:
            return u'%(actor)s %(verb)s %(action_object)s %(timesince)s ago' % ctx
        return u'%(actor)s %(verb)s %(timesince)s ago' % ctx

    def timesince(self, now=None):
        from django.utils.timesince import timesince as timesince_
        return timesince_(self.timestamp, now)

    @property
    def slug(self):
        return id2slug(self.id)

    def mark_as_read(self):
        if self.unread:
            # self.unread = False
            # self.save()
            self.delete()

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save()
    
    @classmethod
    def check_repeatation(self):
        return self.id


def notify_handler(verb, **kwargs):
    """
    Handler function to create Notification instance upon action signal call.
    """
    # Pull the options out of kwargs
    kwargs.pop('signal', None)
    recipient = kwargs.pop('recipient')
    actor = kwargs.pop('sender')
    optional_objs = [
        (kwargs.pop(opt, None), opt)
        for opt in ('target', 'action_object')
    ]
    public = bool(kwargs.pop('public', True))
    action_url = kwargs.pop('action_url', '')
    model = kwargs.pop('model', '')
    is_repeated = bool(kwargs.pop('is_repeated', False))
    description = kwargs.pop('description', None)
    timestamp = kwargs.pop('timestamp', timezone.now())
    level = kwargs.pop('level', 'info')

    # Check if User or Group
    if isinstance(recipient, Group):
        recipients = recipient.user_set.all()
    elif isinstance(recipient, (QuerySet, list)):
        recipients = recipient
    else : recipients = [recipient]

    new_notification = []

    for recipient in recipients:
        notificationObj = Notification.objects.filter(model=model, verb=str(verb), unread=True, deleted=False, recipient=recipient).last() if is_repeated else ''

        if notificationObj:
            new_notification = []

            d_text = []
            for text in description.split():
                if text.isdigit():
                    text = int(text) + 1
                    d_text.append(str(text))
                else:
                    d_text.append(text)
            des_text = " ".join(d_text)

            notificationObj.description = des_text
            notificationObj.timestamp = timestamp
            notificationObj.save()

            new_notification.append(notificationObj)
        else:
            newnotify = Notification.objects.create(
                recipient=recipient,
                actor_content_type=ContentType.objects.get_for_model(actor),
                actor_object_id=actor.pk,
                verb=str(verb),
                public=public,
                description=description,
                timestamp=timestamp,
                level=level,
                action_url=action_url,
                model=model,
            )

            # Set optional objects
            for obj, opt in optional_objs:
                if obj is not None:
                    setattr(newnotify, '%s_object_id' % opt, obj.pk)
                    setattr(newnotify, '%s_content_type' % opt,
                            ContentType.objects.get_for_model(obj))

            if kwargs and EXTRA_DATA:
                newnotify.data = kwargs

            newnotify.save()
            new_notification.append(newnotify)

    return new_notification


# connect the signal
notify.connect(notify_handler, dispatch_uid='notification.models.notification')
