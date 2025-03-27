from django.utils.safestring import mark_safe
from django import template
from datetime import datetime
from textwrap import wrap
import math
from django.utils.html import strip_tags
from ngoasset.models import AssetItem

register = template.Library()

@register.simple_tag
def specification(item=None, spec_id=None, with_html=True):
     if isinstance(item, int): item = AssetItem.objects.get(id=item)
     specification = ""
     if item:
          try:
               spec = item
               if spec.item_code: specification += "<b>Code</b> : " + str(spec.item_code) + ", "
               if spec.specification: specification += "<b>Specification</b> : " + str(spec.specification[:100]) + ('..' if len(spec.specification) > 100 else '') + ", "
               if spec.brand: specification += "<b>Brand</b> : " + str(spec.brand) + ", "
               if spec.model: specification += "<b>Model</b> : " + str(spec.model) + ", "
               if spec.origin: specification += "<b>Origin</b> : " + str(spec.origin) + ", "
          except: pass
     if with_html: return mark_safe(specification)
     else: return strip_tags(mark_safe(specification))