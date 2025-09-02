from sys import audit
from django.urls import path
from . import views
from hr.views import  *
app_name='hr'

urlpatterns = [
     # path('eligible-employee-list/', views.pf_employee_eligible, name='employee_list'),
     path('employee/import/', views.import_employee, name='import_employee'),
     path('employee-add/', views.employee_add, name='employee_add'),
     path('employee/update-requests/', views.update_requests, name='update_requests'),
     path('ajax/get-update-request-data/', views.get_update_requests_for_dataTable, name='get_update_requests_for_dataTable'),
     path('ajax/get-update-request-info/', views.get_update_request_info, name='get_update_request_info'),
     path('ajax/update-request-info/', views.update_request_info, name='update_request_info'),
     path('employee/<str:employee_id>/', views.employee_view, name='employee_view'),
     path('employee/update-status/', views.updateEmployeeStatus, name='updateEmployeeStatus'),
     path('employee/<str:employee_id>/update/', views.employee_update, name='employee_update'),
     path('get-employees/', views.get_employees, name='get_employees'),
     
     path('pf_master_add/', views.pf_master_add, name='pf_master_add'),
     path('pf_master/<int:id>/update/', views.pf_master_update, name='pf_master_update'),
     path('pf_master/<int:id>/delete/', views.delete_pf_master, name='pf_master_delete'),

     # path('pf-policy-master-list/', views.pf_policy_master_list, name='pf_policy_master_list'),
     path('pf-policy-master-add/', views.pf_policy_master_add, name='pf_policy_master_add'),
     path('pf-policy/<int:id>/update/', views.pf_policy_master_update, name='pf_policy_master_update'),
     path('pf-policy/<int:id>/delete/', views.delete_pf_policy_master, name='pf_policy_master_delete'),

     path('emp-eligible-list/', views.pf_eligible_list, name='emp_eligible_list'),
     path('pf-emp-enroll-list/', views.pf_employee_enrollment_list, name='pf_emp_enroll_list'),
     path('get-employee-enroll-list-filter/', views.get_employee_enrollment_list_filter, name='get_employee_enrollment_list_filter'),
     path('employee-pf-add/<int:id>/', views.employee_pf_add, name='employee_pf_add'),
     path('employee-pf-update/<int:id>/update/', views.employee_pf_update, name='employee_pf_update'),
     path('employee-pf/<int:id>/delete/', views.delete_employee_pf, name='employee_pf_delete'),
     path('employee/pf/import/', views.import_employee_in_pf, name='import_employee_in_pf'),

     path('pf-discontinue/', views.pf_discontinue, name='pf_discontinue'),
     path('get-pf-discontinue/', views.get_pf_discontinue, name='get_pf_discontinue'),

     path('emp-transfer-log/', views.employee_transfer_log, name='employee_transfer_log'),
     path('get-employee-transfer-list-filter/', views.get_employee_transfer_list_filter, name='get_employee_transfer_list_filter'),
     path('employee-transfer/', views.employee_transfer, name='employee_transfer'),
     path('get-employee-transfer/', views.get_employee_transfer, name='get_employee_transfer'),
     # path('transfer-pf-info/', views.transfer_pf_info, name='transfer_pf_info'),
     path('get-contribution-filter/', views.get_contribution_filter, name='get_contribution_filter'),
     path('pf-contribution-log/', views.pf_contribution_log, name='pf_contribution_log'),
     path('pf-contribution/', views.pf_contribution, name='pf_contribution'),
     path('get-pf-contribution/', views.get_contribution, name='get_contribution'),

     # For loan module
     path('employee-loan-eligible-list/', views.loan_eligible_list, name='loan_eligible_list'),
     path('loan-setup/<int:id>/', views.pf_loan_setup, name='loan_setup'),
     path('loan-update/<int:id>/update/', views.pf_loan_update, name='loan_update'),
     path('loan-list/', views.loan_list, name='loan_list'),
     path('loan-schedule/<int:id>/', views.loan_schedule, name='loan_schedule'),
     path('loan-reschedule/<int:id>/', views.loan_reschedule, name='loan_reschedule'),
     # path('get-loan-info/', views.get_loan_info, name='get_loan_info'),
     path('get-loan-filter/', views.get_loan_filter, name='get_loan_filter'),

     #Complience URLS
     path('license-entry/', views.licinse_entry, name='licinse_entry'),
     path('license/<int:id>/update/', views.license_entry_update, name='license_entry_update'),
     path('license-view/<int:id>/view/', views.license_view, name='license_view'),

     path('audit-entry/', views.audit_status_entry, name='audit_status_entry'),
     path('audit/<int:id>/update/', views.audit_status_update, name='audit_status_update'),
     path('audit-view/<int:id>/view/', views.audit_status_view, name='audit_status_view'),

     # HolidaySetup
     path('holiday-setup/', views.holiday_setup_list, name='holiday_setup_list'),
     path('holiday-setup/edit/<int:id>/', views.holiday_setup_update, name='holiday_setup_update'),
     path('holiday-setup/delete/<int:id>/', views.holiday_setup_delete, name='holiday_setup_delete'),
     path('holiday-setup-update-fixed-status/', views.holiday_setup_update_fixed_status, name='holiday_setup_update_fixed_status'),

     # Holiday
     path('branch-wise-weekends/', views.company_weekends, name='company_weekends'),
     path('ajax/get-company-weekends-data/', views.get_weekend_data, name='get_weekend_data'),

     path('holiday/', views.holiday_list, name='holiday_list'),
     # path('holiday/edit/<int:id>/', views.holiday_update, name='holiday_update'),
     # path('holiday/delete/<int:id>/', views.holiday_delete, name='holiday_delete'),
     path('holiday-calendar/', views.holiday_calendar, name='holiday_calendar'),
     path('ajax/get-holiday-calendar-data/', views.get_calendar_data, name='get_calendar_data'),
     path('ajax/get-holiday-company-data/', views.get_holiday_company_data, name='get_holiday_company_data'),

     # NoticeBoard
     path('notice-board/', views.notice_board_list, name='notice_board_list'),
     path('notice-board/edit/<int:id>/', views.notice_board_update, name='notice_board_update'),
     path('notice-board/delete/<int:id>/', views.notice_board_delete, name='notice_board_delete'),
     path('notice-board-update-status/', views.notice_update_status, name='notice_update_status'),

     # Salary Process
     path('salary-breakdown/', views.salary_breakdown, name='salary_breakdown'),
     path('income-tax-slab/', views.income_tax_slab, name='income_tax_slab'),
     path('income-tax-slab/<int:id>/edit/', views.income_tax_slab_update, name='income_tax_slab_update'),
     path('income-tax-slab/<int:id>/delete/', views.income_tax_slab_delete, name='income_tax_slab_delete'),
     path('import-other-salary-amounts/', views.import_other_salary_amounts, name='import_other_salary_amounts'),
     path('import-gross-salary-amounts/', views.import_gross_salary_amounts, name='import_gross_salary_amounts'),
     path('salary-process2/', views.salary_process2, name='salary_process2'),
     path('salary-process/', views.salary_process, name='salary_process'),
     path('salary/report/', views.salary_report, name='salary_report'),
     path('ajax/salary-report-data/', views.get_salary_report, name='get_salary_report'),
     # path('festival-bonus/', views.festival_bonus, name='festival_bonus'),
     # path('ajax/festival-report-data/', views.get_festival_report, name='get_festival_report'),
     path('salary/branch-wise-summary-report/', views.branch_wise_summary_report, name='branch_wise_summary_report'),
     path('ajax/get-branch-wise-summary-report/', views.get_branch_wise_salary_summary_report, name='get_branch_wise_salary_summary_report'),
     path('salary/branch-wise-details-report/', views.branch_wise_details_report, name='branch_wise_details_report'),
     path('ajax/get-branch-wise-details-report/', views.get_branch_wise_details_report, name='get_branch_wise_details_report'),
     path('salary/branch-wise-deduct-summary-report/', views.branch_wise_deduct_summary_report, name='branch_wise_deduct_summary_report'),
     path('ajax/get-branch-wise-deduct-summary-report/', views.get_branch_wise_deduct_summary_report, name='get_branch_wise_deduct_summary_report'),
     path('salary/bank-format/', views.bank_format_report, name='bank_format_report'),
     path('ajax/get-bank-format/', views.get_bank_format_report, name='get_bank_format_report'),


     path('pay-slip/', views.pay_slip, name='pay_slip'),
     path('ajax/payslip-report-data/', views.get_payslip_report, name='get_payslip_report'),
     path('ajax/get-employee-data-for-salry-process/', views.get_employee_data_for_salary_process, name='get_employee_data_for_salary_process'),
     path('ajax/get-salary-process-for-datatable/', views.get_salary_process_for_datatable, name='get_salary_process_for_datatable'),
     path('salary-process/delete/<int:id>/', views.salary_process_delete, name='salary_process_delete'),
     path('salary-process/<int:id>/', views.salary_process_view, name='salary_process_view'),


     # Salary Structure
     path('salary-structures/', views.salary_structure_list, name='salary_structure_list'),
     path('salary-structures/<int:id>/edit/', views.salary_structure_update, name='salary_structure_update'),
     path('salary-structures/<int:id>/delete/', views.salary_structure_delete, name='salary_structure_delete'),

     # Salary Slabs
     path('salary-slabs/', views.salary_slab_list, name='salary_slab_list'),
     path('salary-slabs/edit/<int:id>/', views.salary_slab_update, name='salary_slab_update'),
     path('salary-slabs/delete/<int:id>/', views.salary_slab_delete, name='salary_slab_delete'),

     # Salary Heads
     path('salary-heads/', views.salary_head_list, name='salary_head_list'),
     path('salary-heads/edit/<int:id>/', views.salary_head_update, name='salary_head_update'),
     path('salary-heads/delete/<int:id>/', views.salary_head_delete, name='salary_head_delete'),

     # Salary Grade
     path('salary-grades/', views.salary_grade_list, name='salary_grade_list'),
     path('salary-grades/edit/<int:id>/', views.salary_grade_update, name='salary_grade_update'),
     path('salary-grades/delete/<int:id>/', views.salary_grade_delete, name='salary_grade_delete'),

     # Salary Grade-Step
     path('salary-steps/', views.salary_step_list, name='salary_step_list'),
     path('salary-steps/edit/<int:id>/', views.salary_step_update, name='salary_step_update'),
     path('salary-steps/delete/<int:id>/', views.salary_step_delete, name='salary_step_delete'),

     # Leave Type
     path('leave-type/', views.leave_type_list, name='leave_type_list'),
     path('leave-type/edit/<int:id>/', views.leave_type_update, name='leave_type_update'),
     path('leave-type/delete/<int:id>/', views.leave_type_delete, name='leave_type_delete'),
     path('leave-type-update-status/', views.leave_type_update_status, name='leave_type_update_status'),
     path('leave-type-update-payable-status/', views.leave_type_update_payable_status, name='leave_type_update_payable_status'),

     # Leave Master
     path('leave-master/', views.leave_master_list, name='leave_master_list'),
     path('leave-master/edit/<int:id>/', views.leave_master_update, name='leave_master_update'),
     path('leave-master/delete/<int:id>/', views.leave_master_delete, name='leave_master_delete'),
     path('leave-master-update-status/', views.leave_master_update_status, name='leave_master_update_status'),
     path('leave/import/', views.import_leaves, name='import_leaves'),
     path('leave/import-balance/', views.import_leave_balance, name='import_leave_balance'),
     path('leave-allocation/list/', views.leave_allocation_list, name='leave_allocation_list'),

     path('ajax/leave-allocation/list/', views.get_leave_allocation_for_datatable, name='get_leave_allocation_for_datatable'),
     path('leave-allocation/company-wise/', views.leave_allocation_company_wise, name='leave_allocation_company_wise'),
     path('leave-allocation/user-wise/', views.leave_allocation_user_wise, name='leave_allocation_user_wise'),

     # Leave Application
     path('leave-application/', views.leave_application, name='leave_application'),
     path('ajax-get-leave-application-list/<str:list_type>/<str:has_approval>/', views.get_leave_applications_for_dataTable, name='get_leave_applications_for_dataTable'),
     path('leave-application-approval/', views.leave_application_approval, name='leave_application_approval'),

     # Location
     path('location/', views.location_list, name='location_list'),
     path('location/edit/<int:id>/', views.location_update, name='location_update'),
     path('location/delete/<int:id>/', views.location_delete, name='location_delete'),
     path('ajax/location/status-update/', views.location_update_status, name='location_update_status'),

     # Building
     path('building/', views.building_list, name='building_list'),
     path('building/edit/<int:id>/', views.building_update, name='building_update'),
     path('building/delete/<int:id>/', views.building_delete, name='building_delete'),
     path('ajax/building/status-update/', views.building_update_status, name='building_update_status'),
     path('ajax/get-company-wise-location/', views.get_company_wise_location, name='get_company_wise_location'),
     path('ajax/get-location-wise-building/', views.get_location_wise_building, name='get_location_wise_building'),
     path('ajax/get-building-wise-floor/', views.get_building_wise_floor, name='get_building_wise_floor'),

     # Shift
     path('shift/', views.shift_list, name='shift_list'),
     path('ajax/shift-update-status/', views.shift_update_status, name='shift_update_status'),
     path('shift/edit/<int:id>/', views.shift_update, name='shift_update'),
     path('shift/delete/<int:id>/', views.shift_delete, name='shift_delete'),
     path('shift-roster/', views.shift_roaster, name='shift_roaster'),
     path('ajax/get-employee-data-for-shift-roster/', views.get_employee_data_for_shift_roaster, name='get_employee_data_for_shift_roaster'),
     path('ajax/get-rosters-data/', views.get_roasters_for_dataTable, name='get_roasters_for_dataTable'),
     path('rosters-shift/edit/<int:id>/', views.roaster_update, name='roaster_update'),
     path('rosters-shift/delete/<int:id>/', views.roaster_delete, name='roaster_delete'),
     path('ajax/get-data-for-shift-roster/', views.get_roaster_data, name='get_roaster_data'),

     # Employee
     path('ajax/employee-personal-info/', views.employee_personal_info, name='employee_personal_info'),
     path('ajax/get-department-wise-section/', views.get_department_wise_section, name='get_department_wise_section'),
     path('ajax/get-company-wise-floor/', views.get_company_wise_floor, name='get_company_wise_floor'),
     path('ajax/get-division-wise-sub_section/', views.get_division_wise_sub_section, name='get_division_wise_sub_section'),
     path('ajax/get-company-wise-holidays/', views.get_company_wise_holidays, name='get_company_wise_holidays'),
     path('ajax/get-building-wise-hrfloor/', views.get_building_wise_hrfloor, name='get_building_wise_hrfloor'),
     path('ajax/get-company-wise-line/', views.get_company_wise_line, name='get_company_wise_line'),
     path('ajax/get-company-and-floor-wise-line/', views.get_company_and_floor_wise_line, name='get_company_and_floor_wise_line'),
     path('ajax/get-all-shift/', views.get_all_shift, name='get_all_shift'),
     path('ajax/get-company-and-location-wise-shift/', views.get_company_and_location_wise_shift, name='get_company_and_location_wise_shift'),
     path('ajax/employee-official-info/', views.employee_official_info, name='employee_official_info'),
     path('ajax/get-company-and-location-wise-building/', views.get_company_and_location_wise_building, name='get_company_and_location_wise_building'),
     path('ajax/employee-nominee-info/', views.employee_nominee_info, name='employee_nominee_info'),
     path('ajax/employee-bank-info/', views.employee_bank_info, name='employee_bank_info'),
     path('ajax/get-employee-for-datatable/', views.get_employee_for_datatable, name='get_employee_for_datatable'),
     path('ajax/get-incomplete-employees-for-datatable/', views.get_incomplete_employees_for_datatable, name='get_incomplete_employees_for_datatable'),
     path('ajax/email-duplicate-check/', views.email_duplicate_check, name='email_duplicate_check'),
     path('employee/edit/<int:id>/', views.employee_edit, name='employee_edit'),
     path('ajax/employee-update-status/', views.employee_update_status, name='employee_update_status'),
     path('ajax/employee-info-update-status/', views.employee_info_update_status, name='employee_info_update_status'),

     path('sync-attendance/', views.sync_attendance, name='sync_attendance'),
     path('get-attendance-data-from-devices/', views.get_attendance_data_from_devices, name='get_attendance_data_from_devices'),
     path('attendance/list/', views.attendance_list, name='attendance_list'),
     path('attendance/entry/', views.attendance_entry, name='attendance_entry'),
     path('attendance/import/', views.import_attendances, name='import_attendances'),
     path('attendance/import-device-data-attendance/', views.import_device_data_attendances, name='import_device_data_attendances'),
     path('attendance/monthly-report/', views.attendance_report, name='attendance_report'),
     path('ajax/get-monthly-report-data/', views.get_monthly_report_data, name='get_monthly_report_data'),
     path('attendance/daily-report/', views.daily_attendance_report, name='daily_attendance_report'),
     path('ajax/get-job-card-data/', views.get_job_card_data, name='get_job_card_data'),
     path('attendance/job-card/', views.job_card, name='job_card'),
     path('attendance/my-job-card/', views.my_job_card, name='my_job_card'),
     path('attendance/my-job-card/<str:employee_id>/', views.my_job_card, name='my_job_card'),
     path('attendance/my-job-card/<str:employee_id>/<str:start_date>/<str:end_date>/', views.my_job_card, name='my_job_card'),
     path('ajax/daily-attendance-report-data/', views.get_daily_attendance_report_data, name='get_daily_attendance_report_data'),
     path('attendance/device-data/', views.get_device_data, name='get_device_data'),
     path('attendance-devices/', views.attendance_devices, name='attendance_devices'),
     path('get-attendance-devices/', views.get_attendance_devices, name='get_attendance_devices'),
     path('fetch-attendance-devices/', views.fetch_attendance_devices, name='fetch_attendance_devices'),
     path('import-attendance-devices/', views.import_attendance_devices, name='import_attendance_devices'),
     path('outside-remote-duty/', views.outside_remote_duty, name='outside_remote_duty'),
     path('outside-duty-approve/<int:id>/', views.outside_duty_approve, name='outside_duty_approve'),
     path('outside-duty-reject/<int:id>/', views.outside_duty_reject, name='outside_duty_reject'),
     path('outside-duty/<int:id>/delete/', views.outside_duty_delete, name='outside_duty_delete'),

     path('mp-budget/', views.mp_budget, name='mp_budget'),
     path('mp-budget-create/', views.mp_budget_create, name='mp_budget_create'),
     path('mp-budget-edit/', views.mp_budget_edit, name='mp_budget_edit'),
     path('mp-budget-approval/', views.mp_budget_approval, name='mp_budget_approval'),
     path('ajax/get-mp-budget-details/', views.get_mp_budget_details, name='get_mp_budget_details'),
     path('mpb-view/', views.mpb_view, name='mpb_view'),
     path('ajax/check-exists-mp-budget/', views.check_exists_mp_budget, name='check_exists_mp_budget'),
     path('delete-mp-budget/', views.delete_mp_budget, name='delete_mp_budget'),
     path('ajax/get-mp-budget-for-datatable/<str:tab_name>/', views.get_mp_budget_for_datatable, name='get_mp_budget_for_datatable'),

     # start recruitment
     path('recruitment/', views.recruitment, name='recruitment'),
     path('recruitment-create/', views.recruitment_create, name='recruitment_create'),
     path('recruitment-edit/', views.recruit_edit, name='recruit_edit'),
     path('ajax/get-employee-data/', views.get_employee_data, name='get_employee_data'),
     path('ajax/get-check-man-power-budget-data/', views.get_check_man_power_budget, name='get_check_man_power_budget'),
     path('ajax/get-check-man-power-budget-data-designation-wise/', views.get_check_man_power_budget_designation_wise, name='get_check_man_power_budget_designation_wise'),
     path('recruit-view/', views.recruit_view, name='recruit_view'),
     path('recruit-approval/', views.recruit_approval, name='recruit_approval'),
     path('ajax/get-recruit-for-datatable/<str:tab_name>/', views.get_recruit_for_datatable, name='get_recruit_for_datatable'),

     # HRSalaryCycle
     path('hr_salary_cycle/', views.hr_salary_cycle_list, name='hr_salary_cycle_list'),
     path('hr_salary_cycle/edit/<int:id>/', views.hr_salary_cycle_update, name='hr_salary_cycle_update'),
     path('hr_salary_cycle/delete/<int:id>/', views.hr_salary_cycle_delete, name='hr_salary_cycle_delete'),
     path('ajax-cycle-update-status/', views.cycle_update_status, name='cycle_update_status'),



     # Company Unit
     path('company_unit/', views.company_unit_list, name='company_unit_list'),
     path('company_unit/edit/<int:id>/', views.company_unit_update, name='company_unit_update'),
     path('company_unit/delete/<int:id>/', views.company_unit_delete, name='company_unit_delete'),

     # HRFloor
     path('hr_floor/', views.hr_floor_list, name='hr_floor_list'),
     path('hr_floor/edit/<int:id>/', views.hr_floor_update, name='hr_floor_update'),
     path('hr_floor/delete/<int:id>/', views.hr_floor_delete, name='hr_floor_delete'),


     # HRAttendanceBonusRule
     path('festival-bonus/', views.bonus_setup, name='bonus_setup'),
     path('festival-bonus/edit/<int:id>/', views.bonus_setup_update, name='bonus_setup_update'),
     path('festival-bonus/delete/<int:id>/', views.bonus_delete, name='bonus_delete'),


     # HRTiffinBillRule
     path('hr_tiffin_bill_rule/', views.hr_tiffin_bill_rule_list, name='hr_tiffin_bill_rule_list'),
     path('hr_tiffin_bill_rule/edit/<int:id>/', views.hr_tiffin_bill_rule_update, name='hr_tiffin_bill_rule_update'),
     path('hr_tiffin_bill_rule/delete/<int:id>/', views.hr_tiffin_bill_rule_delete, name='hr_tiffin_bill_rule_delete'),


     # Loan
     path('loan/', views.loan_list, name='loan_list'),
     path('loan/edit/<int:id>/', views.loan_update, name='loan_update'),
     path('loan/delete/<int:id>/', views.loan_delete, name='loan_delete'),

     # Appraisal  get_appraisal_data
     path("appraisal/entry/", views.appraisal_entry, name="appraisal_entry"),
     path("appraisal/list/", views.appraisal_list, name="appraisal_list"),
     path("appraisal/get-data/", views.get_appraisal_data, name="get_appraisal_data"),
     path("appraisal/reject/", views.reject_appraisal, name="reject_appraisal"),
     path("appraisal/print/<int:id>/", views.appraisal_print, name="appraisal_print"),



     # Division
     path('division/', views.division_list, name='division_list'),
     path('division/edit/<int:id>/', views.division_update, name='division_update'),
     path('division/delete/<int:id>/', views.division_delete, name='division_delete'),
     path('ajax/division/status-update/', views.division_update_status, name='division_update_status'),



     # SubSection
     path('sub_section/', views.sub_section_list, name='sub_section_list'),
     path('sub_section/edit/<int:id>/', views.sub_section_update, name='sub_section_update'),
     path('sub_section/delete/<int:id>/', views.sub_section_delete, name='sub_section_delete'),
     path('ajax/sub_section/status-update/', views.sub_section_update_status, name='sub_section_update_status'),

     # FiscalYear
     path('fiscal_year/', views.fiscal_year_list, name='fiscal_year_list'),
     path('fiscal_year/edit/<int:id>/', views.fiscal_year_update, name='fiscal_year_update'),
     path('fiscal_year/delete/<int:id>/', views.fiscal_year_delete, name='fiscal_year_delete'),
     path('ajax/fiscal-year-update-status/', views.fiscal_year_update_status, name='fiscal_year_update_status'),
     path('separation-management/', views.separation_management, name='separation_management'),
     path('movement-registry/', views.movement_registry, name='movement_registry'),
     path('cessation/action/', views.employee_cessation_action, name='employee_cessation_action'),
     path('promotion-demotion/', views.promotion_demotion, name='promotion_demotion'),
     path('promotion-history-view/', views.promotion_history_view, name='promotion_history_view'),

     # employee branch wise transfer
     path('employee-transfer-branchwise/', views.employee_transfer_branchwise, name='employee_transfer_branchwise'),
     path('employee-transfer-branchwise/<int:id>/edit/', views.employee_transfer_branchwise_update, name='employee_transfer_branchwise_update'),
]