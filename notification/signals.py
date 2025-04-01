''' Django notifications signal file '''
# -*- coding: utf-8 -*-
from django.dispatch import Signal

# notify = Signal(providing_args=[  # pylint: disable=invalid-name
#     'recipient', 'actor', 'verb', 'action_object', 'target', 'description',
#     'timestamp', 'level', 'action_url', 'model', 'is_repeated',
# ])
notify = Signal()
