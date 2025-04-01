from django.utils.timesince import timesince
from general.models import Users
from django.shortcuts import render
from django import get_version
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView
# from notification import settings
from notification.models import Notification
from notification.utils import id2slug, slug2id
# from notification.settings import get_config
from django.views.decorators.cache import never_cache
from django.http import JsonResponse


class NotificationViewList(ListView):
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    # paginate_by = settings.get_config()['PAGINATE_BY']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(NotificationViewList, self).dispatch(
            request, *args, **kwargs)


class AllNotificationsList(NotificationViewList):

    def get_queryset(self):
        user = Users.objects.get(id=self.request.session.get('id'))
        notifications = Notification.objects.filter(recipient=user)

        # if settings.get_config()['SOFT_DELETE']:
        #     qset = notifications.active()
        # else:
        #     qset = notifications.all()
        # return qset
        return True

class UnreadNotificationsList(NotificationViewList):

    def get_queryset(self):
        user = Users.objects.get(id=self.request.session.get('id'))
        notifications = Notification.objects.filter(recipient=user)
        return notifications.unread()


@login_required
def mark_all_as_read(request):
    
    user = Users.objects.get(id=request.session.get('id'))
    notifications = Notification.objects.filter(recipient=user)
    notifications.mark_all_as_read()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)
    return redirect('notifications:unread')


def mark_as_read(request, slug=None):
    print(slug)

    notification_id = slug2id(slug)
    user = Users.objects.get(id=request.session.get('id'))
    notification = get_object_or_404(
        Notification, recipient=user, id=notification_id)
    

    notification.mark_as_read()

    return JsonResponse({'status':"success"})


@login_required
def mark_as_unread(request, slug=None):

    notification_id = slug2id(slug)
    user = Users.objects.get(id=request.session.get('id'))
    notification = get_object_or_404(
        Notification, recipient=user, id=notification_id)
    notification.mark_as_unread()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)

    return redirect('notifications:unread')


@login_required
def delete(request, slug=None):

    notification_id = slug2id(slug)
    user = Users.objects.get(id=request.session.get('id'))
    notification = get_object_or_404(
        Notification, recipient=user, id=notification_id)

    # if settings.get_config()['SOFT_DELETE']:
    #     notification.deleted = True
    #     notification.save()
    # else:
    #     notification.delete()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)

    return redirect('notifications:all')


@never_cache
def live_unread_notification_count(request):

    user = Users.objects.get(id=request.session.get('id'))
    notifications = Notification.objects.filter(recipient=user)

    data = {
        'unread_count': notifications.unread().count(),
    }
    return JsonResponse(data)


@never_cache
def live_unread_notification_list(request):

    default_num_to_fetch = get_config()['NUM_TO_FETCH']
    try:
        num_to_fetch = request.GET.get('max', default_num_to_fetch)
        num_to_fetch = int(num_to_fetch)
        if not (1 <= num_to_fetch <= 100):
            num_to_fetch = default_num_to_fetch
    except ValueError:  # If casting to an int fails.
        num_to_fetch = default_num_to_fetch

    unread_list = []

    user = Users.objects.get(id=request.session.get('id'))
    notifications = Notification.objects.filter(recipient=user)

    for notification in notifications.unread()[0:num_to_fetch]:
        struct = model_to_dict(notification)
        struct['slug'] = id2slug(notification.id)
        if notification.actor:
            struct['actor'] = str(notification.actor)
        if notification.target:
            struct['target'] = str(notification.target)
        if notification.action_object:
            struct['action_object'] = str(notification.action_object)
        struct['timesince'] = notification.timesince()
        struct['slug'] = notification.slug
        unread_list.append(struct)
        if request.GET.get('mark_as_read'):
            notification.mark_as_read()
    data = {
        'unread_count': notifications.unread().count(),
        'unread_list': unread_list
    }
    return JsonResponse(data)


@never_cache
def live_all_notification_list(request):

    default_num_to_fetch = get_config()['NUM_TO_FETCH']
    try:
        num_to_fetch = request.GET.get('max', default_num_to_fetch)
        num_to_fetch = int(num_to_fetch)
        if not (1 <= num_to_fetch <= 100):
            num_to_fetch = default_num_to_fetch
    except ValueError:
        num_to_fetch = default_num_to_fetch

    all_list = []

    user = Users.objects.get(id=request.session.get('id'))
    notifications = Notification.objects.filter(recipient=user)

    for notification in notifications.all()[0:num_to_fetch]:
        struct = model_to_dict(notification)
        struct['slug'] = id2slug(notification.id)
        if notification.actor:
            struct['actor'] = str(notification.actor)
        if notification.target:
            struct['target'] = str(notification.target)
        if notification.action_object:
            struct['action_object'] = str(notification.action_object)
        all_list.append(struct)
        if request.GET.get('mark_as_read'):
            notification.mark_as_read()
    data = {
        'all_count': notifications.count(),
        'all_list': all_list
    }
    return JsonResponse(data)


def live_all_notification_count(request):

    user = Users.objects.get(id=request.session.get('id'))
    notifications = Notification.objects.filter(recipient=user)

    data = {
        'all_count': notifications.count(),
    }
    return JsonResponse(data)


def all_unread_list(request):
    user = Users.objects.get(id=request.session.get('id'))
    notifications = Notification.objects.filter(recipient=user)
    unread_list = []

    for notification in notifications.unread():
        struct = model_to_dict(notification)
        struct['slug'] = id2slug(notification.id)
        if notification.actor:
            struct['actor'] = str(notification.actor)
        if notification.target:
            struct['target'] = str(notification.target)
        if notification.action_object:
            struct['action_object'] = str(notification.action_object)
        struct['timesince'] = notification.timesince()
        struct['slug'] = notification.slug
        unread_list.append(struct)
    context = {
        'unread_count': notifications.unread().count(),
        'unread_list': unread_list
    }
    return render(request, 'notifications/unread_list.html', context)
