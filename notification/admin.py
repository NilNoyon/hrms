import inspect
from django.contrib import admin
from notification import models

for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj):
        try:
            admin.site.register(obj)
        except:
            pass