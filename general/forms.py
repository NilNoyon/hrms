from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import *
from hr.models import EmployeeInfo


class UserAddForm(forms.ModelForm):

    class Meta:
        model = Users
        fields = ('name', 'employee_id', 'password', 'password_text', 'email', 'branch', 'department',
                  'designation', 'role','secondary_role','secondary_company', 'helpdesk_role', 'status', 'reporting_to', 'is_department_head')
        widgets = {
            'password': forms.PasswordInput()
        }

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['password_text'].required = False

class MyProfileUpdate(forms.ModelForm):

    class Meta:
        model = EmployeeInfo
        fields = ('first_name','last_name','father_name','email','phone_no','photo','signature','date_of_birth', 
                  'gender','religion','blood_group','nationality','birth_certificate','nid','passport','marital_status',
                  'spouse_name','no_of_children','permanent_address','present_address')

class BankForm(forms.ModelForm):
    is_foreign      = forms.BooleanField(required=False)
    class Meta:
        model       = Bank
        fields      = '__all__'

class ApprovalLogForm(forms.ModelForm):

    class Meta:
        model       = ApprovalLog
        fields      = '__all__'

        
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = '__all__'

# Departments
class DepartmentsForm(forms.ModelForm):
	class Meta:
		model = Departments
		fields = '__all__'

# Designations
class DesignationsForm(forms.ModelForm):
	class Meta:
		model = Designations
		fields = '__all__'

# Sections
class SectionsForm(forms.ModelForm):
	class Meta:
		model = Sections
		fields = '__all__'

class CommonLogForm(forms.ModelForm):
    class Meta:
        model = CommonLogs
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(CommonLogForm, self).__init__(*args, **kwargs)
        self.fields['ip_address'].required = False

