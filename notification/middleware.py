from general.models import Users
from notification.models import *

class NotificationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response    = self.get_response(request)
        action_url  = request.path
        user        = request.session.get('id', '')
        try:
            userObj     = Users.objects.get(id=user)
            unread_notifications = Notification.objects.filter(recipient=userObj, unread=True, action_url=action_url)
            if unread_notifications.count() > 0 : unread_notifications.delete()
        except : pass
        return response