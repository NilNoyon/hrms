from django.contrib import admin
from desk.models import *

class IssueAdmin(admin.ModelAdmin):
    list_display  = ['ref','description','issuer', 'status']
    search_fields = ['ref','description','issuer__employee_id','status']
    list_filter   = ['status']
    raw_id_fields = ("issuer",)


# class EmployeeAdmin(admin.ModelAdmin):
#     list_display  = ['employee_id','name','designation','department', 'email','phone']
#     search_fields = ['employee_id','designation','department','email','phone']
#     list_filter   = ['company','department','designation']

class DeviceAssessmentsAdmin(admin.ModelAdmin):
    list_display  = ['assessment_for','device_type','device','created_at','status']
    search_fields = ['assessment_for__employee_id','device_type','device','status']
    list_filter   = ['status','device','device_type']
    raw_id_fields = ("assessment_for",)

admin.site.register(Issue, IssueAdmin)
admin.site.register(DeviceAssessments, DeviceAssessmentsAdmin)
admin.site.register(AssessmentDeviceList)
