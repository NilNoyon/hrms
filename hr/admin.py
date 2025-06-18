from django.contrib import admin
from hr.models import *

class EmployeeInfoAdmin(admin.ModelAdmin):
     list_display  = ['employee_id','first_name','last_name','phone_no','status']
     search_fields = ['employee_id','email','phone_no']
     # list_filter   = ['employee_id','first_name','last_name']
     list_per_page = 100
     raw_id_fields = ("gender","religion","marital_status")
admin.site.register(EmployeeInfo, EmployeeInfoAdmin)

class EmployeeDetailsAdmin(admin.ModelAdmin):
     list_display  = ['branch_name', 'employee_id', 'name', 'location','designation','department','office_mobile','has_pf','status']
     search_fields = ['branch__name','location__name','department__name','personal__employee_id', 'punch_id']
     list_filter   = ['branch',]
     list_per_page = 1000
     raw_id_fields = ("branch", "division", "sub_section", "department", "branch","reporting_to", "designation", "section", "personal","shift", "employee_type", "employee_category", "skill_category", "created_by","updated_by", "status", "location", "cost_center", "unit", "attendance_bonus")

     def name(self, obj):
          return str(obj.name) or "N/A"
     def branch_name(self, obj):
          return str(obj.branch.short_name)
admin.site.register(EmployeeDetails, EmployeeDetailsAdmin)

class EmployeeNomineeAdmin(admin.ModelAdmin):
     list_display  = ['employee','nominee_name','nominee_nid', 'relation', 'share_of_right']
     search_fields = ['employee','nominee_name','nominee_nid']
     raw_id_fields = ['created_by', 'updated_by', 'status', 'employee']
admin.site.register(EmployeeNominee, EmployeeNomineeAdmin)

class EmployeeBankInfoAdmin(admin.ModelAdmin):
     list_display  = ['employee','bank_name','branch_name', 'account_no', 'created_by']
     search_fields = ['employee','bank_name','account_no']
     raw_id_fields = ['created_by', 'updated_by', 'status', 'employee']
admin.site.register(EmployeeBankInfo, EmployeeBankInfoAdmin)

class employee_info(admin.ModelAdmin):
     pass

class ProvidentFundAdmin(admin.ModelAdmin):
     list_display  = ['pf_heading','pf_registation_no','date_of_formation'] 

admin.site.register(ProvidentFundMaster,ProvidentFundAdmin)
class provident_fund_master(admin.ModelAdmin):
     pass

admin.site.register(PolicyMaster)
class policy_master(admin.ModelAdmin):
     pass

class EmployeePFAdmin(admin.ModelAdmin):
     list_display  = ['employee','pf','policy','basic_gross_salary','date_Pf_membership'] 
admin.site.register(EmployeePF,EmployeePFAdmin)
class employee_pf(admin.ModelAdmin):
     pass

class PFDiscontinueAdmin(admin.ModelAdmin):
    list_display  = ['employee_pf','reason','date_discontinuation']
    list_filter   = ['employee_pf']
admin.site.register(PFDiscontinue,PFDiscontinueAdmin)
class pf_discontinue(admin.ModelAdmin):
     pass

class EmployeeTransferAdmin(admin.ModelAdmin):
     list_display  = ['employee','employee_pf','department_from','department_to','designation_from','designation_to','effictive_from_date']
admin.site.register(EmployeeTransfer,EmployeeTransferAdmin)
class employee_transfer(admin.ModelAdmin):
     pass

class PFContributionAdmin(admin.ModelAdmin):
     list_display  = ['employee_pf','emp_percent','branch_percent','gross_salary','contribution_amount']
     list_filter   = ['employee_pf']
admin.site.register(PFMonthlyContribution,PFContributionAdmin)
class pf_monthly_contribution(admin.ModelAdmin):
     pass

class PFLoanSetupAdmin(admin.ModelAdmin):
     list_display  = ['employee','created_at','emi_start_date','loan_amount','emi_months']
     list_filter   = ['employee']
admin.site.register(PFLoanSetup,PFLoanSetupAdmin)
class pf_loan_setup(admin.ModelAdmin):
     pass

admin.site.register(LicenseInfo)
admin.site.register(AuditStatus)


class HRLeaveTypeAdmin(admin.ModelAdmin):
     list_display  = ['short_title', 'description', 'created_by', 'status']
     search_fields = ['short_title', 'description']
     raw_id_fields = ['created_by', 'updated_by', 'status']
admin.site.register(HRLeaveType, HRLeaveTypeAdmin)

class HRLeaveMasterAdmin(admin.ModelAdmin):
     list_display  = ['branch_sname', 'leave_type', 'employee_type', 'employee_category', 'allocated_days', 'created_by', 'status']
     raw_id_fields = ['branch', 'leave_type', 'employee_type', 'employee_category', 'created_by', 'updated_by', 'status']
     def branch_sname(self, obj):
          return str(obj.branch.short_name)
admin.site.register(HRLeaveMaster, HRLeaveMasterAdmin)

class HRLeaveAllocationAdmin(admin.ModelAdmin):
     list_display  = ['employee', 'leave', 'fiscal_year', 'allocated_days', 'availed_days', 'applied_days', 'created_by', 'status']
     search_fields = ['employee__personal__employee_id']
     list_filter   = ['leave__leave_type', 'employee__branch__short_name',  'fiscal_year__name',]
     raw_id_fields = ['employee', 'leave', 'fiscal_year', 'created_by', 'updated_by', 'status']
admin.site.register(HRLeaveAllocation, HRLeaveAllocationAdmin)

class HRLeaveApplicationAdmin(admin.ModelAdmin):
     list_display  = ['application_no', 'employee', 'leave', 'reporting_boss', 'dept_head', 'hr', 'created_by', 'status']
     raw_id_fields = ['employee', 'leave', 'reporting_boss', 'dept_head', 'hr', 'created_by', 'updated_by', 'status']
admin.site.register(HRLeaveApplication, HRLeaveApplicationAdmin)

class HRAttendanceAdmin(admin.ModelAdmin):
     list_display  = ['employee', 'emp_name', 'location', 'shift', 'present_day', 'in_time', 'out_time', 'ot_hours', 'created_by', 'created_at', 'status']
     list_filter   = ['employee__branch','shift',]
     search_fields = ['employee__personal__employee_id']
     raw_id_fields = ['employee', 'location', 'shift', 'created_by', 'updated_by', 'status']
     def emp_name(self, obj):
          return obj.employee.personal.name
admin.site.register(Attendance, HRAttendanceAdmin)

class HRAttendanceLogAdmin(admin.ModelAdmin):
     list_display  = ['attendance', 'device', 'card_id', 'log_time', 'created_by', 'status']
     raw_id_fields = ['attendance', 'device', 'created_by', 'updated_by', 'status']
     list_filter   = [('log_time', admin.DateFieldListFilter),]
admin.site.register(AttenddanceLog, HRAttendanceLogAdmin)

class HRAttendanceDeviceAdmin(admin.ModelAdmin):
     list_display  = ['device_id', 'location', 'building', 'floor', 'name', 'ip_address', 'created_by', 'status']
     raw_id_fields = ['location', 'building', 'floor', 'created_by', 'updated_by', 'status']
admin.site.register(AttendanceDevice, HRAttendanceDeviceAdmin)

class EmployeeCalendarAdmin(admin.ModelAdmin):
     list_display  = ['calendar_day', 'employee', 'attendance', 'absent', 'is_weekend', 'is_holiday', 'in_leave', 'is_late', 'leave_application', 'created_at']
     search_fields = ['employee__personal__employee_id', 'leave_application__application_no']
     raw_id_fields = ['employee', 'leave_application', 'attendance']
     list_filter   = ['employee__branch',]
admin.site.register(EmployeeCalendar, EmployeeCalendarAdmin)

class HolidayAdmin(admin.ModelAdmin):
     list_display  = ['setup', 'name', 'start_date', 'end_date', 'is_mail_send']
     list_filter   = ['branch','setup',]
     raw_id_fields = ['branch', 'setup', 'created_by', 'updated_by', 'status']
admin.site.register(Holiday, HolidayAdmin)

class HolidayIndividualsAdmin(admin.ModelAdmin):
    list_display  = ['holiday', 'holiday_date', 'created_by', 'updated_by', 'status']
    list_filter   = ['holiday__setup',]
    raw_id_fields = ['holiday', 'created_by', 'updated_by', 'status']
admin.site.register(HolidayIndividuals, HolidayIndividualsAdmin)

class HRSalaryBreakdownAdmin(admin.ModelAdmin):
     list_display  = ['employee', 'slab_heads', 'amount', 'created_by', 'status']
     list_filter   = ['slab_heads','employee__branch', 'employee__employee_category']
     raw_id_fields = ['employee', 'slab_heads', 'created_by', 'updated_by', 'status']
admin.site.register(HRSalaryBreakdown, HRSalaryBreakdownAdmin)

class HRMontlySalaryDetailsAdmin(admin.ModelAdmin):
     list_display  = ['year', 'month', 'heads', 'employee', 'amount', 'created_by', 'status']
     list_filter   = ['year', 'month', 'heads']
     search_fields = ['employee__personal__employee_id']
     raw_id_fields = ['employee', 'heads', 'created_by', 'updated_by', 'status']
admin.site.register(HRMontlySalaryDetails, HRMontlySalaryDetailsAdmin)

class AppraisalAdmin(admin.ModelAdmin):
     list_display  = ['appraisee', 'coo_user', 'grand_total', 'status', 'created_by', 'created_at']
     search_fields = ['appraisee__personal__employee_id']
     raw_id_fields = ['appraisee', 'coo_user', 'chairman_user', 'created_by', 'updated_by', 'status']
     list_filter   = ['appraisee__branch',]
admin.site.register(Appraisal, AppraisalAdmin)
admin.site.register(EmployeePromotionDemotion)
admin.site.register(PromotionDemotionHistory)
admin.site.register(MovementRegistry)

import inspect
from hr import models


for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj):
        try     : admin.site.register(obj)
        except  : pass