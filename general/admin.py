from django.contrib import admin
from django.apps import apps
from general.models import *

class CompanyAdmin(admin.ModelAdmin):
    list_display  = ['short_name', 'name', 'address']
    search_fields = ['name', 'short_name']

class BranchAdmin(admin.ModelAdmin):
    list_display  = ['short_name', 'name', 'address']
    search_fields = ['name', 'short_name']

class UserAdmin(admin.ModelAdmin):
    list_display  = ['employee_id','name','designation','department', 'email','role','helpdesk_role']
    search_fields = ['employee_id','name','designation__name','branch__name','department__name','email','role__name','helpdesk_role']
    list_filter   = ['branch','department','role', 'helpdesk_role','is_department_head']
    raw_id_fields = ["designation","department","branch","role","reporting_to"]

class MenuListAdmin(admin.ModelAdmin):
    list_display  = ['module_name','menu_name','is_sub_menu','sub_menu_name','menu_url','menu_icon','menu_order','status']
    search_fields = ['module_name','menu_name','menu_url','menu_icon','menu_order']
    list_filter   = ['module_name','status','is_sub_menu'] 

class MenuPermissionAdmin(admin.ModelAdmin):
    list_display  = ['menu','user','view_action','insert_action','update_action','delete_action','status']
    search_fields = ['user__name','menu__menu_name','menu__menu_url','user__employee_id','menu__module_name']
    list_filter   = ['status','menu__module_name','menu__is_sub_menu']
    raw_id_fields = ["menu",'user']

class ForgotPasswordAdmin(admin.ModelAdmin):
    list_display  = ['email','created_at','is_used']
    search_fields = ['email','is_used']
    list_filter   = ['is_used']
    date_hierarchy = "created_at"

class CommonMasterAdmin(admin.ModelAdmin):
    list_display  = ['value','value_for','ordering','status']
    search_fields = ['value','value_for','status']
    list_filter   = ['value_for','status']
    date_hierarchy = "created_at"


class BuyerAdmin(admin.ModelAdmin):
    list_display  = ['name','short_name','phone_no', 'country','status','premium']
    search_fields = ['name','short_name']
    list_filter   = ['name','status']

class BankAdmin(admin.ModelAdmin):
    list_display  = ['name','branch']
    search_fields = ['name','branch']
    list_filter   = ['name']

class SectionsAdmin(admin.ModelAdmin):
    list_display = ['department', 'name']
    search_fields = ['department__name', 'name']
    list_filter = ['department']
    raw_id_fields = ["department","created_by"]


admin.site.register(Company, CompanyAdmin)
admin.site.register(Departments)
admin.site.register(Sections, SectionsAdmin)
admin.site.register(Designations)
admin.site.register(UserRoles)
admin.site.register(Users, UserAdmin)
admin.site.register(MenuList, MenuListAdmin)
admin.site.register(UserPermission, MenuPermissionAdmin)
admin.site.register(ForgotPassword,ForgotPasswordAdmin)
admin.site.register(CommonMaster,CommonMasterAdmin)
admin.site.register(Status)
admin.site.register(Branch,BranchAdmin)


class ApprovalLogAdmin(admin.ModelAdmin):
    list_display  = ['model', 'reference', 'ref_id', 'approved_rejected_by', 'status', 'approved_rejected_date','status_message']
    list_filter   = ['model', 'status__title']
    raw_id_fields = ['status', 'status_message', 'approved_rejected_by']
    search_fields = ['model', 'reference', 'approved_rejected_by__name']
    # list_editable = ('approved_rejected_date',)
admin.site.register(ApprovalLog, ApprovalLogAdmin)

class CommonLogsAdmin(admin.ModelAdmin):
    list_display  = ['content_type', 'description', 'log_at', 'log_by']
    list_filter   = ['status', 'previous_status']
    raw_id_fields = ['content_type', 'log_by']
    search_fields = ['description']

admin.site.register(CommonLogs, CommonLogsAdmin)
admin.site.register(Bank, BankAdmin)


from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.urls import reverse
from django.utils.safestring import mark_safe
class LogEntryAdmin(admin.ModelAdmin):
    list_display  = ['user', 'content_type', 'object_link', 'action_flag','action_time']
    list_filter   = ['user']
    search_fields = ['object_repr', 'change_message']

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return mark_safe(link)
    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"
admin.site.register(LogEntry, LogEntryAdmin)
