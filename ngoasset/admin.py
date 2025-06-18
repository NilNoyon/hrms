from django.contrib import admin
from .models import *
from ngoasset import models
import inspect

class AssetAdmin(admin.ModelAdmin):
    list_display  = ['code', 'item', 'sub_classification', 'supplier', 'asset_user', 'asset_controller']
    search_fields = ['code', 'item__item_master__item_name', 'sub_classification__value', 'asset_user__name', 'asset_controller__name']
    raw_id_fields = ['updated_by','status','created_by','branch', 'item', 'sub_classification', 'supplier', 'asset_user', 'asset_controller','currency','bank', 'department_or_cost_center']
admin.site.register(models.Asset, AssetAdmin)

class AssetAllocationAdmin(admin.ModelAdmin):
    list_display  = ['asset_user', 'asset_location', 'revalution_value']
    search_fields = ['asset_user__name', 'asset_location', 'revalution_value']
    raw_id_fields = ['asset', 'asset_user', 'cost_center', 'created_by']
admin.site.register(models.FAAssetAllocation, AssetAllocationAdmin)
