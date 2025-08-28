from dataclasses import fields
from importlib.metadata import files
from django.forms import ClearableFileInput
from django import forms
from hr.models import *

class Pf_EmployeeForm(forms.ModelForm):
    class Meta:
        model = EmployeeInfo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(Pf_EmployeeForm, self).__init__(*args, **kwargs)
        self.fields['employee_id'].required = False
        self.fields['nid'].required = False
        self.fields['birth_certificate'].required = False
        self.fields['passport'].required = False
        
class EmployeeDetailsForm(forms.ModelForm):
    class Meta:
        model = EmployeeDetails
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(EmployeeDetailsForm, self).__init__(*args, **kwargs)
        self.fields['punch_id'].required = False
        self.fields['personal'].required = False
        self.fields['section'].required = False
        self.fields['location'].required = False
        self.fields['shift'].required = False
        self.fields['confirmation_date'].required = False
        self.fields['separation_date'].required = False
        self.fields['employee_type'].required = False
        self.fields['employee_category'].required = False
        self.fields['skill_category'].required = False
        self.fields['provision_month'].required = False
        self.fields['reporting_to'].required = False
        self.fields['unit'].required = False
        self.fields['attendance_bonus'].required = False

class EmployeeNomineeForm(forms.ModelForm):
    class Meta:
        model = EmployeeNominee
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(EmployeeNomineeForm, self).__init__(*args, **kwargs)
        self.fields['employee'].required = False
        self.fields['share_of_right'].required = False
        self.fields['nominee_nid'].required = False

class EmployeeBankForm(forms.ModelForm):
    class Meta:
        model = EmployeeBankInfo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(EmployeeBankForm, self).__init__(*args, **kwargs)
        self.fields['employee'].required = False

class ProvidentFundMasterForm(forms.ModelForm):
    class Meta:
        model = ProvidentFundMaster
        fields = ('branch','pf_heading','pf_registation_no','date_of_formation','basis_of_pf_computation','basis_of_accounting',
        'mode_of_loan_interest','rate_employee','rate_company','opening_balance_of_lapse_forfeiture','service_lenght',
        'income_distribution_mode','hight_limit_of_contribution','day_wise_contribution_calculation','ex_member_fund',
        'multipul_loan')

    # def __init__(self, *args, **kwargs):
    #     self.full_clean()

class PolicyMasterForm(forms.ModelForm):
    class Meta:
        model = PolicyMaster
        fields ="__all__"

    # def __init__(self, *args, **kwargs):
    #     self.full_clean()

class EmpPfRegistationForm(forms.ModelForm):
    class Meta:
        model = EmployeePF
        # fields = ('employee','basis_of_contribution','basic_gross_salary','rate_employee_contribution',
        # 'rate_company_contribution','emp_opening_contribution',
        # 'company_opening_contribution','emp_opening_balance_interest','company_opening_balance_interest')
        fields = "__all__"

class PFDiscontinueForm(forms.ModelForm):
    class Meta:
        model = PFDiscontinue
        fields = "__all__"
class EmployeeCessationForm(forms.ModelForm):
    class Meta:
        model = EmployeeCessation
        fields = ('emolpoyee','effective_from_date','cessation_reason','letter_type','letter','created_by','updated_by')

class EmployeePromotionDemotionForm(forms.ModelForm):
    class Meta:
        model = EmployeePromotionDemotion
        fields = "__all__"
        exclude = ('approved_by', 'approved_at')
class EmployeeTransferForm(forms.ModelForm):
    class Meta:
        model = EmployeeTransfer
        fields = "__all__"


class PfContributionForm(forms.ModelForm):
    class Meta:
        model = PFMonthlyContribution
        fields = ('employee_pf','is_round','Voucher_no','emp_percent','branch_percent','gross_salary','contribution_amount','entry_date','month','year')

class PFLoanForm(forms.ModelForm):
    class Meta:
        model = PFLoanSetup
        fields = '__all__'

class PFLoanResheduleForm(forms.ModelForm):
    class Meta:
        model = PFLoanReschedulingInfo
        fields = '__all__'
        
class License(forms.ModelForm):
    
    class Meta:

        model = LicenseInfo

        fields = '__all__'



class AuditStatusForm(forms.ModelForm):

    class Meta:

        model = AuditStatus

        fields = '__all__'

# HolidaySetup
class HolidaySetupForm(forms.ModelForm):
	class Meta:
		model = HolidaySetup
		fields = '__all__'

# Holiday
class HolidayForm(forms.ModelForm):
	class Meta:
		model = Holiday
		fields = '__all__'


# NoticeBoard
class NoticeBoardForm(forms.ModelForm):
    class Meta:
        model   = NoticeBoard
        fields  = "__all__"
        widgets = {
            'attachment' : ClearableFileInput(attrs={'multiple': False}),
        }

# Outside/Remote Duty
class OutsideRemoteDutyForm(forms.ModelForm):
	class Meta:
		model = OutsideRemoteDuty
		fields = '__all__'

# Salary Slab Setup
class HRSalarySlabForm(forms.ModelForm):
	class Meta:
		model = HRSalarySlabMaster
		fields = '__all__'
		
class HRSalaryGradeForm(forms.ModelForm):
	class Meta:
		model = HRSalaryGradeMaster
		fields = '__all__'
		
class HRSalaryGradeStepForm(forms.ModelForm):
	class Meta:
		model = HRSalaryGradeStep
		fields = '__all__'
                
# Income Tax Slab Setup
class HRIncomeTaxSlabForm(forms.ModelForm):
	class Meta:
		model = HRIncomeTaxSlabMaster
		fields = '__all__'
                
# Salary Breakdown Setup
class HRSalaryBreakdownForm(forms.ModelForm):
	class Meta:
		model = HRSalaryBreakdown
		fields = '__all__'

# HRLeaveType
class HRLeaveTypeForm(forms.ModelForm):
	class Meta:
		model = HRLeaveType
		fields = '__all__'



# HRLeaveMaster
class HRLeaveMasterForm(forms.ModelForm):
	class Meta:
		model = HRLeaveMaster
		fields = '__all__'



# HRLeaveAlloaction
class HRLeaveAllocationForm(forms.ModelForm):
	class Meta:
		model = HRLeaveAllocation
		fields = '__all__'



# HRLeaveAlloaction
class HRLeaveApplicationForm(forms.ModelForm):
	class Meta:
		model = HRLeaveApplication
		fields = '__all__'



# Location
class LocationForm(forms.ModelForm):
	class Meta:
		model = Location
		fields = '__all__'

# Building
class BuildingForm(forms.ModelForm):
	class Meta:
		model = Building
		fields = '__all__'

# Shift
class ShiftForm(forms.ModelForm):
    class Meta:
        model   = Shift
        fields  = '__all__'

    def __init__(self, *args, **kwargs):
        super(ShiftForm, self).__init__(*args, **kwargs)
        self.fields['branch'].required     = False
        self.fields['location'].required    = False

# Attendance
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(Pf_EmployeeForm, self).__init__(*args, **kwargs)
        self.fields['location'].required = False

# MP Budget
class HRManPowerBudgetForm(forms.ModelForm):
	class Meta:
		model = HRManPowerBudget
		fields = '__all__'

# HR Employee Recruitment
class HREmployeeRecruitmentForm(forms.ModelForm):
	class Meta:
		model = HREmployeeRecruitment
		fields = '__all__'



# HRSalaryCycle
class HRSalaryCycleForm(forms.ModelForm):
	class Meta:
		model = HRSalaryCycle
		fields = '__all__'



# Company Unit
class CommonMasterForm(forms.ModelForm):
	class Meta:
		model = CommonMaster
		fields = '__all__'


# HRFloor
class HRFloorForm(forms.ModelForm):
	class Meta:
		model = HRFloor
		fields = '__all__'


# HRAttendanceBonusRule
class HRAttendanceBonusRuleForm(forms.ModelForm):
	class Meta:
		model = HRAttendanceBonusRule
		fields = '__all__'


# HRTiffinBillRule
class HRTiffinBillRuleForm(forms.ModelForm):
	class Meta:
		model = HRTiffinBillRule
		fields = '__all__'


# HRTiffinBillRule
class HRSalaryProcessForm(forms.ModelForm):
	class Meta:
		model = HRSalaryProcess
		fields = '__all__'



# Loan
class LoanForm(forms.ModelForm):
	class Meta:
		model = Loan
		fields = '__all__'



# Division
class DivisionForm(forms.ModelForm):
	class Meta:
		model = Division
		fields = '__all__'



# SubSection
class SubSectionForm(forms.ModelForm):
	class Meta:
		model = SubSection
		fields = '__all__'



# FiscalYear
class FiscalYearForm(forms.ModelForm):
	class Meta:
		model = FiscalYear
		fields = '__all__'
		
# Employee Branch Transfer
class EmployeeBranchTransferForm(forms.ModelForm):
    class Meta:
        model = EmployeeBranchTransfer
        fields = '__all__'
