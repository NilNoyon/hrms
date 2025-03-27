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

class FAAssetRepairAdmin(admin.ModelAdmin):
    list_display  = ['asset', 'repair_date', 'repair_amount','reason_for_repair','repair_reference','repair_type']
    search_fields = ['asset', 'repair_date','repair_reference','repair_type']
    raw_id_fields = ['asset', 'created_by']
admin.site.register(models.AssetRepair, FAAssetRepairAdmin)

class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display  = ['request_no', 'branch', 'etd','requset_branch','note','delivery_at']
    search_fields = ['request_no', 'branch', 'etd','delivery_at']
    raw_id_fields = ['branch','requset_branch','status', 'created_by']
admin.site.register(models.MaintenanceRequest, MaintenanceRequestAdmin)

class RequestDetailsAdmin(admin.ModelAdmin):
    list_display  = ['maintenance', 'asset','problem_details','assign_to','solve_by','solve_at','delivery_at']
    search_fields = ['maintenance', 'assign_to', 'solve_by','delivery_at']
    raw_id_fields = ['maintenance','asset', 'created_by','assign_by','status','item','assign_to','solve_by']
admin.site.register(models.RequestDetails, RequestDetailsAdmin)

for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj):
        try: admin.site.register(obj)
        except: pass