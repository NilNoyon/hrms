from django import template
from desk.models import Issue, Users
from django.db.models import Q

register = template.Library()

@register.filter # register the template filter with django
def get_string_as_list(value): # Only one argument.
    """Evaluate a string if it contains []"""
    if '[' and ']' in value:
        return eval(value)

@register.filter(name="notification")
def notification_count(userid):
    user = Users.objects.filter(id = userid)
    if user:
        
        if user[0].role == 3 or user[0].role == 4: #Manager and dept. head
            issues = Issue.objects.filter(status=1)
            if issues: return issues.count()
        else: #assgined/resolver
           pass
    return 0

@register.filter(name="comma_split")
def comma_split_load(obj):
    return str(obj).split(",")
