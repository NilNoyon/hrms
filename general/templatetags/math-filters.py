from django import template
import math
from django.db.models import Q

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    "Multiplies the arg and the value"
    if value: return int(value) * int(arg)
    else: return 0

@register.filter(name='float_mul')
def float_mul(value, arg):
    "Multiplies the arg and the value"
    return float(value) * float(arg)

@register.filter(name='sub')
def sub(value, arg):
    "Subtracts the arg from the value"
    return int(value) - int(arg)
sub.is_safe = False

@register.filter(name='div')
def div(value, arg):
    "Divides the value by the arg"
    if int(arg) == 0:
        arg = 1 # due to handle division by zero error
    if type(arg) != int:
        arg = int(arg)
    return int(value) / int(arg)

@register.filter(name='ceil')
def ceil(value):
    "ceil the value by the arg"
    return math.ceil(value)

@register.filter(name='partition')
def partition(thelist, n):
    """
    Break a list into ``n`` pieces. The last list may be larger than the rest if
    the list doesn't break cleanly. That is::

        >>> l = range(10)

        >>> partition(l, 2)
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

        >>> partition(l, 3)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9]]

        >>> partition(l, 4)
        [[0, 1], [2, 3], [4, 5], [6, 7, 8, 9]]

        >>> partition(l, 5)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

    """
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    p = len(thelist) / n
    return [thelist[p*i:p*(i+1)] for i in range(n - 1)] + [thelist[p*(i+1):]]

@register.simple_tag
def variable_assign_tag(val=None):
    return val
@register.simple_tag
def variable_assign_tag2(val=None):
    return val

@register.simple_tag
def to_int(val=None):
    return val

@register.filter(name='absolute')
def absolute(value):
    "absolute the value"
    return abs(value)

@register.filter(name='modulo')
def modulo(num, val):
    return num % val

@register.filter(name='float_sub')
def float_sub(num, val):
    return round(float(num) - float(val), 2)

@register.filter
def partition(thelist, n):
    try:
        n = int(n)
    except (ValueError, TypeError):
        return [thelist]
    values = list(thelist)
    split = int(ceil(len(values) / n))
    columns = [values[i * split:(i + 1) * split] for i in range(n)]
    return columns

@register.filter(name='replace_dash')
def replace_dash(string):
    return string.replace("-", " ")

@register.filter(name='concat_string')
def concat_string(value_1, value_2):
    return str(value_1) +'_'+ str(value_2)

@register.filter(name='round_to')
def round_to(value):
    "round the value"
    value = float(value) if value else 0
    return round(value,2)

@register.simple_tag
def to_float(val=None):
    return float(val)

@register.filter(name='float_add')
def float_add(value, arg):
    "addition of the float arg and the float value"
    return round(float(value) + float(arg), 3)

@register.filter(name='absolute_to')
def absolute_to(value):
    "absolute the value"
    if value < 0:
        value = value * (-1)
    return value

@register.filter(name='get_value_from_dict')
def get_value_from_dict(dict_data=None, key=None):
    if dict_data and key:
        return dict_data.get(key)
    else: return ' '

@register.filter(name='intchar')
def intchar(value):
    "intword to intchar. Ex: 1.56 millions to 1.56 M"
    if value and type(value).__name__ not in ['int', int]:
        number_in_word = value.split(' ')
        if len(number_in_word) > 1:
            return str(number_in_word[0]) + ' ' + str(number_in_word[1][0]).upper()
        else:
            return value
    elif value:
        return value
    else:
        return 0

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(list(dictionary.keys())[0]).get(key)
