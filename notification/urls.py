# ''' Django notification urls file '''
#  -*- coding: utf-8 -*-
from . import views
from django.urls import re_path as pattern


urlpatterns = [
    pattern(r'^$', views.AllNotificationsList.as_view(), name='all'),
    pattern(r'^unread/$', views.UnreadNotificationsList.as_view(), name='unread'),
    pattern(r'^mark-all-as-read/$', views.mark_all_as_read, name='mark_all_as_read'),
    pattern(r'^mark-as-read/(?P<slug>\d+)/$', views.mark_as_read, name='mark_as_read'),
    pattern(r'^mark-as-unread/(?P<slug>\d+)/$', views.mark_as_unread, name='mark_as_unread'),
    pattern(r'^delete/(?P<slug>\d+)/$', views.delete, name='delete'),
    pattern(r'^api/unread_count/$', views.live_unread_notification_count, name='live_unread_notification_count'),
    pattern(r'^api/all_count/$', views.live_all_notification_count, name='live_all_notification_count'),
    pattern(r'^api/unread_list/$', views.live_unread_notification_list, name='live_unread_notification_list'),
    pattern(r'^api/all_list/', views.live_all_notification_list, name='live_all_notification_list'),
    pattern(r'^unread_list/', views.all_unread_list, name='all_unread_list'),
]

app_name = 'notifications'
