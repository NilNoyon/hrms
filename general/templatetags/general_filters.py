from django.utils.safestring import mark_safe
from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag
def variable_assign_tag(val=None):
    return val

@register.filter
def strip_single_quote(quoted_string):
    return quoted_string.replace("'", "’") if quoted_string else ''

@register.simple_tag
def strip_single_quote_tag(quoted_string):
    return quoted_string.replace("'", "’") if quoted_string else ''
    
@register.filter
def strip_double_quotes(quoted_string):
    return quoted_string.replace('"', "”") if quoted_string else ''

from django.conf import settings

@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")

@register.filter(name='string_to_list')
def string_to_list(value, separator=' '):
    "Collect a string with ' ' (space) separator and make them a list"
    return value.split(separator)
string_to_list.is_safe = False

@register.filter(name='add_float')
def add_float(value, arg):
    "Addition the arg from the value"
    value = float(value) if value else 0
    if arg:
        return round(float(value) + float(arg), 6)
    else:
        return float(value)
add_float.is_safe = False