from email.policy import default
from django.conf import settings
from django.db import models
from django.db.models.deletion import CASCADE
from django_countries.fields import CountryField
from general.models import *
from django.core.validators import MaxValueValidator, MinValueValidator
from django_countries.fields import CountryField
from django.urls import reverse
import os, time
from functools import partial


def _update_filename(instance, filename, Path):
     extension   = "." + filename.split('.')[-1]

     if instance._meta.model == EmployeeInfo : 
          return os.path.join('{0}'.format(Path), "emp-{}.".format(instance.id) + extension)
     elif instance._meta.model == EmployeeNominee : 
          print("A")
          return os.path.join('{0}'.format(Path), "emp-{}.".format(instance.id) + extension)
     else:
          Year        = time.strftime("%Y", time.localtime())
          Month       = time.strftime("%m", time.localtime())
          if instance._meta.model == HRLeaveApplication : 
               code    = instance.application_no.replace("/", '-')
          elif instance._meta.model == NoticeBoard : 
               code    = "Notice" + str(NoticeBoard.objects.count() + 1)
          
          filename    = code + extension
          return os.path.join('{0}/{1}/{2}'.format(Path, Year, Month), filename)

def upload_to(Path):
     return partial(_update_filename, Path=Path)

# Division
class GEOLocation(models.Model):
     division_en = models.CharField(max_length = 50, blank=True, null=True, default=None)
     division_bn = models.CharField(max_length = 50, blank=True, null=True, default=None)
     district_en = models.CharField(max_length = 100, blank=True, null=True, default=None)
     district_bn = models.CharField(max_length = 100, blank=True, null=True, default=None)
     thana_en    = models.CharField(max_length = 100, blank=True, null=True, default=None)
     thana_bn    = models.CharField(max_length = 100, blank=True, null=True, default=None)
     post_office_en = models.CharField(max_length = 100, blank=True, null=True, default=None)
     post_office_bn = models.CharField(max_length = 100, blank=True, null=True, default=None)
     postcode_en = models.CharField(max_length = 10, blank=True, null=True, default=None)
     postcode_bn = models.CharField(max_length = 10, blank=True, null=True, default=None)

     class Meta:
          db_table            = "geo_locations"
          verbose_name        = "GEO Location"
          verbose_name_plural = "GEO Locations" 

     @property
     def location_en(self):
          return "PO : " + str(self.post_office_en) + " - " + str(self.postcode_en) + ", " + \
               str(self.thana_en) + ", " + str(self.district_en)

     @property
     def location_bn(self):
          return  "ডাকঘরঃ " + str(self.post_office_bn) + " - " + str(self.postcode_bn) + ", " + \
               str(self.thana_bn) + ", " + str(self.district_bn)

class FiscalYear(CoreActionWithUpdate):
     name                    = models.CharField(max_length=20, unique=True)
     start_date              = models.DateField()
     end_date                = models.DateField()
     is_active               = models.BooleanField(default=False)

     class Meta:
          ordering            = ['-start_date']
          verbose_name        = "Fiscal Year"
          verbose_name_plural = "Fiscal Years"

     def __str__(self):
          return self.name

     def duration(self):
          """Returns the number of days in the fiscal year."""
          return (self.end_date - self.start_date).days + 1


# Division
class Division(CoreActionWithUpdate):
     name                    = models.CharField(max_length = 200)

     class Meta:
          db_table            = 'hr_divisions'
          verbose_name        = "Division"
          verbose_name_plural = "Divisions" 

     def __str__(self):
          return f'{self.name}'

# Building
class SubSection(CoreActionWithUpdate):
     name        = models.CharField(max_length = 100)
     division    = models.ForeignKey(Division, related_name="sub_sections", on_delete=models.CASCADE, blank=True, null=True)

     class Meta:
          db_table            = 'hr_sub_sections'
          verbose_name        = "SubSection"
          verbose_name_plural = "SubSections" 

     def __str__(self):
          return f'{self.name}'

# Locations
class Location(CoreActionWithUpdate):
     name    = models.CharField(max_length = 200)
     branch  = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)

     class Meta:
          db_table = 'hr_locations'
          verbose_name = "Location"
          verbose_name_plural = "Locations" 

     def __str__(self):
          return f'{self.name}'

# Building
class Building(CoreActionWithUpdate):
     name        = models.CharField(max_length = 100)
     branch      = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
     location    = models.ForeignKey(Location, related_name="bulding_location", on_delete=models.CASCADE, blank=True, null=True)

     class Meta:
          db_table = 'hr_buildings'
          verbose_name = "Building"
          verbose_name_plural = "Buildings" 

     def __str__(self):
          return f'{self.name}'

class HRFloor(CoreActionWithUpdate):
     building    = models.ForeignKey(Building, related_name="building_floor", on_delete=models.CASCADE, blank=True, null=True)
     name        = models.CharField(max_length = 100)

     class Meta:
          db_table            = 'hr_floors'
          verbose_name        = "Floor"
          verbose_name_plural = "Floors" 

     def __str__(self):
          return f'{self.name}'

# Shift
class Shift(CoreActionWithUpdate):
     name            = models.CharField(max_length = 200)
     shift_id        = models.CharField(max_length = 50, blank=True, null=True, default='')
     branch          = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
     location        = models.ForeignKey(Location, related_name="shift_location", on_delete=models.CASCADE, null=True)
     start_time      = models.TimeField(auto_now_add=False, blank=True, null=True) #office start time
     grace_time      = models.TimeField(auto_now_add=False, blank=True, null=True) #grace time 
     end_time        = models.TimeField(auto_now_add=False, blank=True, null=True) #office end time
     day_start       = models.TimeField(auto_now_add=False, blank=True, null=True) #Shift Punch Counting after this time for new day
     buffer_time     = models.TimeField(auto_now_add=False, blank=True, null=True) #Early Leave before this time
     class Meta:
          db_table            = 'hr_shifts'
          verbose_name        = "Shift"
          verbose_name_plural = "Shifts" 

     def __str__(self):
          return f'{self.shift_id}'

     @property
     def title(self):
          return self.name + " ( " + self.get_start_time + " - " + self.get_end_time + " ) "

     @property
     def get_start_time(self):
          return self.start_time.strftime("%I:%M %p") if self.start_time else "N/A"
     @property
     def get_end_time(self):
          return self.end_time.strftime("%I:%M %p") if self.end_time else "N/A"

     @property
     def max_ot(self):
          from datetime import time
          return time(self.ot_end_time) - time(self.ot_start_time)

class EmployeeInfo(CoreActionWithUpdate):
     employee_id         = models.CharField(max_length=20, blank=True, null=True)
     first_name          = models.CharField(max_length=50, blank=True, null=True)
     first_name_bn       = models.CharField(max_length=50, blank=True, null=True)
     last_name           = models.CharField(max_length=50, blank=True, null=True)
     last_name_bn        = models.CharField(max_length=50, blank=True, null=True)
     phone_no            = models.CharField(max_length=15, blank=True, null=True)
     father_name         = models.CharField(max_length=100, blank=True, null=True)
     father_name_bn      = models.CharField(max_length=100, blank=True, null=True)
     father_phone_no     = models.CharField(max_length=15, blank=True, null=True)
     mother_name         = models.CharField(max_length=100, blank=True, null=True)
     mother_name_bn      = models.CharField(max_length=100, blank=True, null=True)
     mother_phone_no     = models.CharField(max_length=100, blank=True, null=True)
     email               = models.CharField(max_length=50, blank=True, null=True)
     date_of_birth       = models.DateTimeField(auto_now_add=False, blank=True, null=True)
     gender              = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="emp_gender", null=True, blank=True, default=None)
     nationality         = models.CharField(max_length=100, blank=True, null=True)
     nid                 = models.CharField(max_length=50, blank=True, null = True)
     birth_certificate   = models.CharField(max_length=50, blank=True, null = True)
     passport            = models.CharField(max_length=50, blank=True, null = True)
     religion            = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="emp_religion", null=True, blank=True, default=None)
     group_type          = (
                              ('N/A', 'N/A'),
                              ('A+', 'A+'),
                              ('A-', 'A-'),
                              ('B+', 'B+'),
                              ('B-', 'B-'),
                              ('AB+', 'AB+'),
                              ('AB-', 'AB-'),
                              ('O+', 'O+'),
                              ('O-', 'O-'),
                              ('Bombay', 'Bombay'),
                              ('INRA', 'INRA'),
                         )
     blood_group         = models.CharField(max_length=10, choices=group_type, default="N/A",blank=True, null = True)
     marital_status      = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="emp_marital_status", null=True, blank=True, default=None)
     spouse_name         = models.CharField(max_length=50, blank=True, null=True)
     spouse_name_bn      = models.CharField(max_length=50, blank=True, null=True)
     spouse_phone_no     = models.CharField(max_length=100, blank=True, null=True)
     no_of_children      = models.IntegerField(default=0, blank=True, null=True)
     permanent_location  = models.ForeignKey(GEOLocation, on_delete=models.CASCADE, related_name="emp_permanent_location", null=True, blank=True, default=None)
     permanent_address   = models.CharField(max_length=1000, blank=True, null=True)
     permanent_address_bn= models.CharField(max_length=1000, blank=True, null=True)
     present_location    = models.ForeignKey(GEOLocation, on_delete=models.CASCADE, related_name="emp_present_location", null=True, blank=True, default=None)
     present_address     = models.CharField(max_length=1000, blank=True, null=True)
     present_address_bn  = models.CharField(max_length=1000, blank=True, null=True)
     photo               = models.ImageField(upload_to=upload_to("employees"), blank=True, null=True)
     signature           = models.ImageField(upload_to=upload_to("employees_sign"), blank=True, null=True)
     reporting_to        = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)
     status              = models.BooleanField(default = True)
     employee_status     = models.ForeignKey('general.Status', on_delete=models.CASCADE, null=True, blank=True)

     class meta:
          db_table            = 'hr_employeeinfo'
          verbose_name        = "Employee"
          verbose_name_plural = "Employee Info"
          
     def __str__(self):
          return str(f"{self.name} {(self.employee_id) or ''}")

     @property
     def name(self):
          return str(f"{self.first_name or ''} {self.last_name or ''}").title()

     @property
     def name_bn(self):
          return str(f"{self.first_name_bn or ''} {self.last_name_bn or ''}").title()

     @property
     def reporting_to_name(self):
          if self.employee_details.last() :
               if user := EmployeeInfo.objects.filter(employee_id=self.employee_details.last().reporting_to).first():
                    return str(f"{user.name} {(user.employee_id) or ''}")
          return "N/A"

     @property
     def emp_details_info(self):
          return EmployeeDetails.objects.filter(employee_id=self.employee_id).first()

class EmployeeDetails(CoreActionWithUpdate):
     employee_id         = models.CharField(max_length=20, blank=True, null=True)
     personal            = models.ForeignKey(EmployeeInfo, related_name="employee_details", on_delete=models.CASCADE, blank=True, null=True, default=None)
     branch              = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
     division            = models.ForeignKey(Division, on_delete=models.CASCADE, blank=True, null=True)
     sub_section         = models.ForeignKey(SubSection, on_delete=models.CASCADE, blank=True, null=True)
     location            = models.ForeignKey(Location, on_delete=models.CASCADE, blank=True, null=True)
     department          = models.ForeignKey(Departments, on_delete=models.CASCADE, blank=True, null=True)
     designation         = models.ForeignKey(Designations, on_delete=models.CASCADE, blank=True, null=True)
     section             = models.ForeignKey(Sections, on_delete=models.CASCADE, blank=True, null=True)
     cost_center         = models.ForeignKey(Branch, related_name="emp_dtls_cost_center", on_delete=models.CASCADE, blank=True, null=True)
     unit                = models.ForeignKey(CommonMaster, on_delete=models.SET_NULL, related_name="emp_dtls_unit", null=True, blank=True, default=None)
     shift               = models.ForeignKey(Shift,on_delete=models.CASCADE, blank=True, null=True)
     reporting_to        = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)
     office_mobile       = models.CharField(max_length=15, blank=True, null=True)
     office_email        = models.CharField(max_length=50, blank=True, null=True)
     punch_id            = models.CharField(max_length=20, blank=True, null=True)
     employee_type       = models.ForeignKey(CommonMaster, on_delete=models.SET_NULL, related_name="emp_dtls_type", null=True, blank=True, default=None)
     employee_category   = models.ForeignKey(CommonMaster, on_delete=models.SET_NULL, related_name="emp_dtls_category", null=True, blank=True, default=None)
     skill_category      = models.ForeignKey(CommonMaster, on_delete=models.SET_NULL, related_name="emp_dtls_skill_category", null=True, blank=True, default=None)
     salary              = models.IntegerField(default=0)
     initial_grade       = models.CharField(max_length=40, blank=True, null=True)
     grade               = models.CharField(max_length=40, blank=True, null=True)
     holiday             = ArrayField(models.CharField(max_length=100), null=True, blank=True, size=100) # Weekend day
     joining_date        = models.DateTimeField(auto_now_add=False, blank=True, null=True)
     confirmation_date   = models.DateTimeField(auto_now_add=False, blank=True, null=True)
     separation_date     = models.DateTimeField(auto_now_add=False, blank=True, null=True)
     provision_months    = (
                              ( '', 'N/A'),
                              ('3', '3'),
                              ('6', '6'),
                              ('9', '9'),
                         )
     provision_month     = models.CharField(max_length=10, choices=provision_months, default="6",blank=True, null = True)
     tin                 = models.CharField(max_length=30, blank=True, null=True)
     pabx                = models.CharField(max_length=10, blank=True, null=True)
     attendance_bonus    = models.ForeignKey('HRAttendanceBonusRule', on_delete=models.CASCADE, blank=True, null=True)
     tiffin_bill         = models.BooleanField(default = False)
     transport_facility  = models.BooleanField(default = False)
     has_pf              = models.BooleanField(default = False)
     overtime            = models.BooleanField(default = False)
     off_day_ot          = models.BooleanField(default = False)
     holiday_bonus       = models.BooleanField(default = False)
     income_tax          = models.BooleanField(default = False)

     def reporting_to_name(self):
          emp = EmployeeDetails.objects.filter(id=self.reporting_to)
          if emp: return str(emp[0].personal.first_name+" "+emp[0].personal.last_name+"("+emp[0].personal.employee_id+")") if emp[0].personal else "N/A"
          else:
               return "N/A"

     class meta:
          db_table = 'hr_employee_details'
          verbose_name = "Employee Detail"
          verbose_name_plural = "Employee Details" 

     def __str__(self):
          return '%s' % (self.personal.employee_id if self.personal else "N/A")

     def get_absolute_url(self):
          return reverse('hr:employee_view', kwargs={'employee_id':self.personal_id})

     @property
     def name(self):
          return self.personal.name if self.personal_id else 'N/A'

     @property
     def name_bn(self):
          return self.personal.name_bn if self.personal_id else 'N/A'

     @property
     def holidays(self):
          days = {
               '0' : 'Monday',
               '1' : 'Tuesday',
               '2' : 'Wednesday',
               '3' : 'Thursday',
               '4' : 'Friday',
               '5' : 'Saturday',
               '6' : 'Sunday'
          }
          return ", ".join([days[d] for d in self.holiday])

     @property
     def current_email(self):
          return self.office_email if self.office_email else ( self.personal.email if self.personal_id and self.personal.email else '' )

     @property
     def current_mobile(self):
          return self.office_mobile if self.office_mobile else ( self.personal.phone_no if self.personal_id and self.personal.phone_no else '' )

     @property
     def user_info(self):
          return Users.objects.filter(employee_id=self.employee_id).order_by('-id').first()

     def save(self, *args, **kwargs):
          if self.joining_date :
               try     : num_of_days = int(self.provision_month) * 30
               except  : num_of_days = 0
               from django.utils import timezone
               from datetime import timedelta, datetime
               current_date, joining_date = timezone.now().date(), self.joining_date
               if type(joining_date) == datetime:
                    joining_date = joining_date.date()
               difference = (current_date - joining_date).days
               if int(difference) > int(num_of_days) :
                    self.confirmation_date = self.joining_date + timedelta(num_of_days)
          super(EmployeeDetails, self).save(*args, **kwargs)

class EmployeeNominee(CoreActionWithUpdate):
     employee            = models.ForeignKey (EmployeeDetails, related_name='nominees', on_delete=models.CASCADE, blank=True, null=True, default=None)
     nominee_name        = models.CharField (max_length=50, blank=True, null=True)
     nominee_nid         = models.CharField (max_length=50, blank=True, null=True)
     relation            = models.CharField (max_length=50, blank=True, null=True)
     nominee_mobile      = models.CharField(max_length=15, blank=True, null=True)
     nominee_address     = models.CharField (max_length=1000, blank=True, null=True)
     share_of_right      = models.CharField (max_length=100, blank=True, null=True)
     nominee_photo       = models.ImageField(upload_to=upload_to("nominee_photo"), blank=True, null=True)

     class meta:
          db_table = 'hr_employee_nominee'
          verbose_name = "Employee Nominee"
          verbose_name_plural = "Employee Nominee" 

     def __str__(self):
          return '%s' % (self.nominee_name)

class EmployeeEducation(CoreActionWithUpdate):
     employee            = models.ForeignKey (EmployeeDetails, on_delete=models.CASCADE, blank=True, null=True, default=None)
     institute           = models.CharField (max_length=500, blank=True, null=True)
     country             = CountryField(null=True, blank=True)
     degree_name         = models.CharField (max_length=200, blank=True, null=True)
     subject             = models.CharField (max_length=200, blank=True, null=True)
     result              = models.CharField(max_length=100,default="",blank=True, null = True)
     pass_year           = models.CharField (max_length=1000, blank=True, null=True)

     class meta:
          db_table = 'hr_employee_education'
          verbose_name = "Employee Education"
          verbose_name_plural = "Employee Educations" 

     def __str__(self):
          return '%s' % (self.degree_name)

class EmployeeExperience(CoreActionWithUpdate):
     employee            = models.ForeignKey (EmployeeDetails, on_delete=models.CASCADE, blank=True, null=True, default=None)
     company_name        = models.CharField (max_length=100, blank=True, null=True)
     company_location    = models.CharField (max_length=500, blank=True, null=True)
     responsibilities    = models.CharField (max_length=1000, blank=True, null=True)
     designation         = models.CharField (max_length=200, blank=True, null=True)
     department          = models.CharField (max_length=200, blank=True, null=True)
     started_date        = models.DateTimeField(auto_now_add=False, blank=True, null=True)
     end_date            = models.DateTimeField(auto_now_add=False, blank=True, null=True)
     is_present          = models.BooleanField(default = False)

     class meta:
          db_table = 'hr_employee_experience'
          verbose_name = "Employee Experience"
          verbose_name_plural = "Employee Experiences" 

     def __str__(self):
          return '%s' % (self.company_name)

class EmployeeBankInfo(CoreActionWithUpdate):
     employee            = models.ForeignKey (EmployeeDetails, related_name='banks', on_delete=models.CASCADE, blank=True, null=True, default=None)
     bank_name           = models.CharField (max_length=500, blank=True, null=True)
     branch_name         = models.CharField (max_length=500, blank=True, null=True)
     account_no          = models.CharField (max_length=50, blank=True, null=True)

     class meta:
          db_table = 'hr_employee_bankinfo'
          verbose_name = "Employee Bank Info"
          verbose_name_plural = "Employee Bank Info" 

     def __str__(self):
          return '%s' % (self.bank_name)
    
class EmployeeUpdateRequest(CoreActionWithUpdate):
     employee                = models.ForeignKey(EmployeeInfo, related_name='emp_request', on_delete=models.CASCADE, blank=True, null=True, default=None)
     data                    = models.JSONField(blank=True, null=True, default=dict)
     model_object            = models.CharField(max_length=50, blank=True, null=True, default=None)

     class meta:
          db_table            = 'hr_employee_update_requests'
          verbose_name        = "Employee Update Request"
          verbose_name_plural = "Employee Update Requests" 

     def __str__(self):
          return '%s' % (self.employee.name)

     @property
     def request_for(self):
          data = ''
          if self.model_object == "EmployeeBankInfo"  : data = 'Bank Info'
          elif self.model_object == "EmployeeNominee" : data = 'Nominee Info'
          return data + " Update"


class ProvidentFundMaster(CoreActionWithUpdate):
     branch             = models.ForeignKey(Branch,on_delete=models.CASCADE,related_name='pf_branch',default='')
     pf_heading         = models.CharField(max_length=100,null=True,blank=True)
     pf_registation_no  = models.IntegerField(unique=True,null=True,blank=True)
     date_of_formation  = models.DateField(auto_now_add=False, null=True, blank=True)
     CHOICES_COMPUTATION= [('--Select--','--Select--'),('On Basic Salary','On Basic Salary'),
          ('On Basic Gross','On Basic Gross')] 
     basis_of_pf_computation = models.CharField(max_length=20, choices=CHOICES_COMPUTATION)
     CHOICES_ACCOUNTING = [('--Select--','--Select--'),('Accrual','Accrual'),
          ('Cash','Cash')]
     basis_of_accounting = models.CharField(max_length=20, choices=CHOICES_ACCOUNTING)
     CHOICE_INTEREST = [('--Select--','--Select--'),('Compound','Compound'),
          ('Simple','Simple'),
          ('Compound and Day Wise','Compound and Day Wise')]
     mode_of_loan_interest = models.CharField(max_length=50, choices=CHOICE_INTEREST)
     rate_employee      = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
     rate_company       = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
     opening_balance_of_lapse_forfeiture = models.IntegerField(null=True,blank=True)
     CHOICES_SERVICE    = [('--Select--','--Select--'),('Date of Joining','Date of Joining'),
          ('Date of Membership','Date of Membership')]
     service_lenght     = models.CharField(max_length=20, choices=CHOICES_SERVICE)
     CHOICE_INCOME      = [('--Select--','--Select--'),('Weighted Distribution','Weighted Distribution'),
          ('Rate 78 Mode','Rate 78 Mode'),
          ('Spacial Distribution','Spacial Distribution')]
     income_distribution_mode = models.CharField(max_length=50, choices=CHOICE_INCOME)
     hight_limit_of_contribution = models.IntegerField(null=True,blank=True)
     CHOICE_CONTRIBUTION = [('--Select--','--Select--'),('YES','YES'),
          ('NO','NO')]
     day_wise_contribution_calculation = models.CharField(max_length=20, default=True, choices=CHOICE_CONTRIBUTION)

     CHOICE_EX_MEMBER    = [('--Select--','--Select--'),('YES','YES'),
          ('NO','NO')]
     ex_member_fund      = models.CharField(max_length=20, choices=CHOICE_EX_MEMBER)
     multipul_loan       = models.BooleanField(default=True)

     def __str__(self):
          return str(self.pf_heading)

     def isDelete(self):
          if  EmployeePF.objects.filter(pf=self.id):
               return False
          else:
               return True

     class meta:
          db_table = 'hr_pf_master'
          verbose_name = "PF"
          verbose_name_plural = "PF Master" 

class PolicyMaster(CoreActionWithUpdate):
     CHOICES_year_form = [('1','1'),
          ('3','3')] 
     effictive_year_from = models.CharField(max_length=30, choices = CHOICES_year_form)
     CHOICES_to_less = [('3','3'),
          ('99','99')]     
     to_less_then        = models.CharField(max_length=30, choices = CHOICES_to_less)
     company_percentage  = models.IntegerField(null=True,blank=True)
     CHOICES_year_form = [('--Select--','--Select--'),('1 to 3','1 to 3'),
          ('3 to 99','3 to 99')] 
     pf_policy_heading   = models.CharField (max_length=50, choices = CHOICES_year_form,default="")

     def __str__(self):
          return str(self.effictive_year_from)+"->"+self.pf_policy_heading

     def isDelete(self):
          if  EmployeePF.objects.filter(policy=self.id):
               return False
          else:
               return True
               
     class meta:
          db_table        = "hr_policy_master"
          verbose_name    = "Policy"
          verbose_name_plural = "Policy Master"

class EmployeePF(CoreActionWithUpdate):
     employee               = models.ForeignKey(EmployeeDetails,on_delete=models.PROTECT)
     pf                     = models.ForeignKey(ProvidentFundMaster,on_delete=models.PROTECT,related_name='emp_pf', null=True,blank=True)
     policy                 = models.ForeignKey(PolicyMaster, on_delete=models.PROTECT,related_name='emp_pf_policy', null=True,blank=True)
     basis_of_contribution  = models.CharField (max_length=100,default="On Basic Salary")
     basic_gross_salary     = models.IntegerField (null=True,blank=True)
     rate_employee_contribution    = models.IntegerField(default="")
     rate_company_contribution     = models.IntegerField(null =True, blank = True)
     date_Pf_membership            = models.DateField(auto_now_add=False , null=True, blank=True)
     emp_opening_contribution      = models.DecimalField (max_digits=50,decimal_places=2)
     company_opening_contribution   = models.DecimalField (max_digits=50,decimal_places=2)
     emp_opening_balance_interest     = models.DecimalField(max_digits=50,decimal_places=2)
     company_opening_balance_interest = models.DecimalField(max_digits=50,decimal_places=2) 
     
     class meta:
          db_table = "hr_employee_pf"
          verbose_name = "Employee PF"
          verbose_name_plural = "Employee PF Info"

     def __str__(self):
          return str(self.employee)

class EmployeeTransfer(CoreActionWithUpdate):
     employee               = models.ForeignKey (EmployeeDetails, on_delete=models.CASCADE)
     employee_pf            = models.ForeignKey (EmployeePF, on_delete=models.CASCADE,null=True, blank=True)
     to_employee_id         = models.CharField (max_length=50,default='')
     effictive_from_date    = models.DateField (auto_now_add=False, null=True, blank=True)
     department_from         =  models.ForeignKey (Departments,on_delete=models.CASCADE, related_name='pf_trans_dept_from')
     department_to           =  models.ForeignKey (Departments,on_delete=models.CASCADE, related_name='pf_trans_dept_to')
     designation_from       =  models.ForeignKey (Designations,on_delete=models.CASCADE, related_name='pf_trans_desig_from')
     designation_to         =  models.ForeignKey (Designations,on_delete=models.CASCADE, related_name='pf_trans_desig_to')
     remarks                = models.CharField(max_length=100, null=True, blank=True)
     email                  = models.CharField(max_length=100)
     joining_date           = models.DateTimeField(auto_now_add=True, null=True, blank=True)


     class meta:
          db_table = "hr_employee_transfer"
          verbose_name = "Employee Transfer"
          verbose_name_plural = "Employee Transfer Info"

     def __str__(self):
          return str(self.employee)

class PFDiscontinue(models.Model):
     employee_pf               = models.ForeignKey(EmployeePF,on_delete=models.CASCADE)
     reason                    = models.CharField (max_length=300)
     lapse_voucher             = models.CharField (max_length=30, null=True , blank= True)
     date_discontinuation      = models.DateTimeField(auto_now_add=True, null=True, blank=True)
     
     class meta:
          db_table = "hr_PF_Discontinue"
          verbose_name = "PF Discontinue"
          verbose_name_plural = "PF Discontinue Info"

month_name = ['','JAN.','FEB.','MAR','APR.','MAY.','JUN.','	JUL.','AUG.','SEP.','OCT.','NOV.','DEC.']

class PFMonthlyContribution(CoreActionWithUpdate):
     employee_pf               = models.ForeignKey(EmployeePF,on_delete=models.CASCADE)
     is_round                  = models.BooleanField(default=False, null=True, blank=True)
     Voucher_no                = models.CharField(max_length=20, null=True , blank=True)
     emp_percent               = models.DecimalField(max_digits=50,decimal_places=2)
     branch_percent            = models.DecimalField(max_digits=50,decimal_places=2)
     gross_salary              = models.IntegerField(default="")
     contribution_amount       = models.IntegerField(default="")
     entry_date                = models.DateTimeField(auto_now_add=False, null=True, blank=True)
     month                     = models.IntegerField(default= 0)
     year                      = models.IntegerField(default= 0)


     class meta:
          db_table = "contribution_info"
          verbose_name = "contribution_info"
          verbose_name_plural = "contributions_info"

     def get_month_name(self):
          return month_name[self.month]
        
class PFLoanSetup(CoreActionWithUpdate):
     pf                              = models.ForeignKey(EmployeePF,on_delete=models.CASCADE)
     employee                        = models.ForeignKey(EmployeeDetails,on_delete=models.CASCADE)
     emi_start_date                  = models.DateTimeField(auto_now_add=False,blank=True,null=True)
     description                     = models.CharField(max_length=100, blank= True, null= True)
     CHOICES  = [('Personal Loans','Personal Loans'),
          ('Auto Loans','Auto Loans'),
          ('Mortgage Loans','Mortgage Loans'),
          ('Home Equity Loans','Home Equity Loans'),
          ('Family Loans','Family Loans'),]
     loan_type                      = models.CharField(max_length=30, choices=CHOICES)
     loan_amount                    = models.FloatField(blank=True, null=True)
     due_amount                     = models.FloatField(blank=True, null=True)
     interest_rate                  = models.IntegerField(blank=True, null=True)
     emi_months                     = models.IntegerField()
     intarest_total_amnount         = models.FloatField(blank=True, null=True) 
     CHOICES  = [('Fixed','Fixed'),
          ('Varible','Varible'),]

     installment_mode               = models.CharField(max_length = 50, choices = CHOICES)
     installment_amount             = models.FloatField(null=True, blank=True)
     per_month_emi_amount           = models.FloatField(null=True, blank=True) 
     rescheduled_counter            = models.IntegerField(default=False, null=True, blank=True)
     is_round                       = models.BooleanField(default=False, null=True, blank=True)

     class meta:
          db_table = "pf_loan_setup"
          verbose_name = "Loan Setup"
          verbose_name_plural = "Loan Setup List"

     def __str__(self):
          return str(self.employee)

class PFLoanReschedulingInfo(models.Model):
     loan                        = models.ForeignKey(PFLoanSetup, on_delete=CASCADE)
     date_of_recheduling         = models.DateTimeField(auto_now_add=False, null=True, blank=True)
     emi_start_date              = models.DateTimeField(auto_now_add=True, null=True, blank=True)
     interest_rate               = models.IntegerField()
     emi_no_of_month             = models.IntegerField()
     due_loan_amount             = models.FloatField()
     due_interest_amount         = models.FloatField()
     CHOICES  = [('Fixt','Fixt'),
          ('Varible','Varible'),]
     installment_mode                = models.CharField(max_length=50, choices=CHOICES)
     rescheduled_monthly_loan_amount = models.FloatField()
     rescheduled_monthly_interest_amount = models.FloatField()
     no_of_due_month                     = models.IntegerField()

     CHOICES = [('1','Pay Interest in last?'),
               ('2','Round')]
     choices = models.CharField(max_length=50, choices=CHOICES, null = True,blank= True)
     status  = models.BooleanField(null=True, blank=True)

     class meta:
          db_table = "pf_loan_rescheduling_info"
          verbose_name = "Loan Rescheduling Info"
          verbose_name_plural = "pf_loan_rescheduling_info"

class PFEmiProcess(models.Model):
     loan                    = models.ForeignKey(PFLoanSetup, on_delete=CASCADE)
     month                   = models.IntegerField()
     year                    = models.IntegerField()
     date                    = models.DateField(auto_now_add=False, null=True, blank=True)

     class meta:
          db_table            = "pf_loan_repayment"
          verbose_name        = "Loan Repayment"
          verbose_name_plural = "pf_loan_repayments"
#Complience Models

class LicenseInfo(models.Model):
     branch            = models.ForeignKey(Branch,on_delete=models.CASCADE)
     license_name      = models.ForeignKey(CommonMaster, default='', on_delete=models.CASCADE)
     certificate_no    = models.CharField(max_length=50)
     issu_date         = models.DateField(auto_now_add=False, null= True, blank=True)
     expire_date       = models.DateField(auto_now_add=False, null= True, blank=True)
     gmail             = ArrayField(models.CharField(max_length=100), null=True, blank=True, size=100)
     renewal_choice    =[('Update','Update'),
                         ('Applied','Applied'),('Parmanent','Parmanent')]
     renewal_status    = models.CharField(max_length=30, choices=renewal_choice)
     attachment        = models.FileField(upload_to="attachment", max_length = 120, blank=True, null=True)
     remarks           = models.CharField(max_length=100,blank=True,null=True)

     class Meta:
          db_table = 'hr_license'
          verbose_name = "license"
          verbose_name_plural = "licenses"

class AuditStatus(models.Model):
     branch            = models.ForeignKey(Branch,on_delete=models.CASCADE)
     name_of_buyer     = models.CharField(max_length=100)
     audit_choice      = [('Social Compliance','Social Compliance'),
     ('Security','Security'),
     ('Tracebility Audit','Tracebility Audit'),
     ('Certification','Certification'),
     ('Enviroment','Enviroment'),
     ('Quality','Quality'),
     ('OHAS','OHAS'),
     ('ILO','ILO'),
     ('COC','COC'),
     ('COP','COP'),
     ('Social','Social'),
     ('COC','COC'),
     ('Safety Audit','Safety Audit')]
     type_of_audit     = models.CharField(max_length=100,choices=audit_choice)
     last_audit_date   = models.DateField(auto_now_add=False, null= True, blank=True)
     expire_date       = models.DateField(auto_now_add=False, null= True, blank=True)
     audit_by_choice   = [('Frist Party','Frist Party'),('Second Party','Second Party'),('Third Party','Third Party')]
     audit_by          = models.CharField(max_length=100,choices=audit_by_choice)
     present_rating    = models.CharField(max_length=100)
     category_choice   = [('Certification Audit','Certification Audit'),('Buyer Audit','Buyer Audit')]
     category          = models.CharField(max_length=50,choices=category_choice)
     remarks           = models.CharField(max_length=250,blank=True,null=True)
     attachment        = models.FileField(upload_to="attachment", max_length = 120, blank=True, null=True)

     class Meta:
          db_table = 'hr_audit_status'
          verbose_name = "Audit Status"
          verbose_name_plural = "hr_audit_status"

class HolidaySetup(CoreActionWithUpdate):
     month_list = (
          ('1', 'January'),
          ('2', 'February'),
          ('3', 'March'),
          ('4', 'April'),
          ('5', 'May'),
          ('6', 'June'),
          ('7', 'July'),
          ('8', 'August'),
          ('9', 'September'),
          ('10', 'October'),
          ('11', 'November'),
          ('12', 'December'),
     )
     name                = models.CharField(max_length=100)
     date                = models.IntegerField(blank=True,null=True)
     month               = models.CharField(max_length=15, choices = month_list,blank=True,null=True)
     fixed               = models.BooleanField(default = True)

     class Meta:
          db_table            = 'hr_holiday_setups'
          verbose_name        = "Holiday Setup"
          verbose_name_plural = "Holiday Setups"

     def __str__(self):
          return str(self.name)

class Holiday(CoreActionWithUpdate):
     branch              = models.ForeignKey(Branch, on_delete=models.SET_NULL, related_name='branch_holiday', null=True, blank=True)
     setup               = models.ForeignKey(HolidaySetup, on_delete=models.SET_NULL, related_name='holiday', null=True,blank=True)
     name                = models.CharField(max_length=100, default='')
     start_date          = models.DateField(auto_now=False, null=True, blank=True)
     end_date            = models.DateField(auto_now=False, null=True, blank=True)
     weekend             = models.BooleanField(default = False)
     is_mail_send        = models.BooleanField(default = True)
     
     class Meta:
          db_table            = 'hr_holidays'
          verbose_name        = "Holiday"
          verbose_name_plural = "Holidays"

     def __str__(self):
          return str(self.company.short_name + " - " + self.name)
     
     
     def save(self, *args, **kwargs):
          super(Holiday, self).save(*args, **kwargs)
          if self.end_date and self.start_date :
               import datetime
               delta, holidays_list = datetime.timedelta(days=1), []
               for date in range((self.end_date - self.start_date).days + 1):
                    current_date = self.start_date + date * delta
                    if hexist := HolidayIndividuals.objects.filter(holiday=self, holiday_date=current_date).first() : 
                         hexist.status = Status.name("active")
                         hexist.save()
                    else : hexist = HolidayIndividuals.objects.create(holiday=self, 
                         holiday_date=current_date, status=Status.name("active"))
                    holidays_list.append(hexist.id)
               HolidayIndividuals.objects.filter(holiday=self).exclude(id__in=holidays_list).delete()


     @property
     def num_of_days(self):
          return (self.end_date - self.start_date).days + 1


class HolidayIndividuals(CoreActionWithUpdate):
     holiday             = models.ForeignKey(Holiday, on_delete=models.SET_NULL, related_name='holiday_indivs', null=True,blank=True)
     holiday_date        = models.DateField(auto_now=False)

     class Meta:
          db_table            = 'hr_holiday_individuals'
          verbose_name        = "Holiday Individual"
          verbose_name_plural = "Holiday Individuals"

     def __str__(self):
          return str(self.holiday.name)
        
class NoticeBoard(CoreActionWithUpdate):
     title               = models.CharField(max_length=200, default='')
     description         = models.TextField(max_length=500, null=True, blank=True)
     start_date          = models.DateTimeField(auto_now=False, null=True, blank=True)
     end_date            = models.DateTimeField(auto_now=False, null=True, blank=True)
     attachment          = models.FileField(upload_to="notices", max_length = 500, blank=True, null=True)

     class Meta:
          db_table            = 'hr_notice_boards'
          verbose_name        = "Notice Board"
          verbose_name_plural = "Notice Board"

     def __str__(self):
          return str(self.title)

class HRLeaveType(CoreActionWithUpdate):
     short_title         = models.CharField(max_length=20, unique=True)
     description         = models.TextField(max_length=200, default='', null=True, blank=True)
     payable             = models.BooleanField(default=True)

     class Meta:
          db_table            = 'hr_leave_types'
          verbose_name        = "Leave Type"
          verbose_name_plural = "Leave Type"

     def __str__(self):
          return self.short_title

class HRSalarySlabMaster(CoreActionWithUpdate):
     slab                = models.ForeignKey(CommonMaster,on_delete=models.SET_NULL, related_name="salary_slab", null=True, blank=True, default=None)
     head                = models.ForeignKey(CommonMaster,on_delete=models.SET_NULL, related_name="salary_head", null=True, blank=True, default=None)
     type_choice         = [('AV','AV'),('AP','AP'), ('DV','DV'),('DP','DP')]
     type                = models.CharField(max_length=20, choices=type_choice)
     start_gross         = models.IntegerField(null=True,blank=True)
     end_gross           = models.IntegerField(null=True,blank=True)
     value_percentage    = models.DecimalField(null=True,blank=True,max_digits=20, decimal_places=2)
     remarks             = models.TextField(max_length=200, default='', null=True, blank=True)

     class Meta:
          db_table            = 'hr_salary_slab_master'
          verbose_name        = "Salary Structure"
          verbose_name_plural = "Salary Structures"

     def __str__(self):
          return self.head.value
    
class HRIncomeTaxSlabMaster(CoreActionWithUpdate):
     from_amount         = models.IntegerField(null=True,blank=True)
     to_amount           = models.IntegerField(null=True,blank=True)
     deduction           = models.IntegerField(null=True,blank=True)
     type_choice         = [('Value','Value'),('Percent','Percent')]
     type                = models.CharField(max_length=20, choices=type_choice)
     remarks             = models.TextField(max_length=200, default='', null=True, blank=True)

     class Meta:
          db_table            = 'hr_income_tax_slab_master'
          verbose_name        = "Income Tax Slab"
          verbose_name_plural = "Income Tax Slabs"

     def __str__(self):
          return str(self.deduction)

class HRSalaryBreakdown(CoreActionWithUpdate):
     employee            = models.ForeignKey(EmployeeDetails,on_delete=models.CASCADE)
     slab_heads          = models.ForeignKey(HRSalarySlabMaster, on_delete=models.CASCADE)
     amount              = models.DecimalField(null=True,blank=True,default=0,max_digits=20, decimal_places=2)

     class Meta:
          db_table            = 'hr_salary_breakdown'
          verbose_name        = "Salary Breakdown"
          verbose_name_plural = "Salary Breakdowns"

     def __str__(self):
          return self.slab_heads.head.value
    
class HRMontlySalaryDetails(CoreActionWithUpdate):
     year               = models.CharField(max_length=4, blank=True, null=True)
     month_list = (
          ('1', 'January'),
          ('2', 'February'),
          ('3', 'March'),
          ('4', 'April'),
          ('5', 'May'),
          ('6', 'June'),
          ('7', 'July'),
          ('8', 'August'),
          ('9', 'September'),
          ('10', 'October'),
          ('11', 'November'),
          ('12', 'December'),
     )
     month              = models.CharField(max_length=15, choices=month_list, blank=True,null=True)
     heads              = models.ForeignKey(HRSalarySlabMaster, on_delete=models.CASCADE)
     employee           = models.ForeignKey(EmployeeDetails,on_delete=models.CASCADE)
     amount             = models.DecimalField(null=True,blank=True,default=0,max_digits=20, decimal_places=2)

     class Meta:
          db_table            = 'hr_monthly_salary_details'
          verbose_name        = "Monthly Salary Detail"
          verbose_name_plural = "Monthly Salary Details"

class HRLeaveMaster(CoreActionWithUpdate):
     branch              = models.ForeignKey(Branch, on_delete=models.CASCADE, default="")
     leave_type          = models.ForeignKey(HRLeaveType, on_delete=models.CASCADE, related_name="hr_leave_type", null=True, blank=True, default=None)
     employee_type       = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="hr_employee_type", null=True, blank=True, default=None)
     employee_category   = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="hr_employee_category", null=True, blank=True, default=None)
     allocated_days      = models.PositiveSmallIntegerField(default=0)


     class Meta:
          db_table            = 'hr_leave_masters'
          verbose_name        = "Leave Master"
          verbose_name_plural = "Leave Master"

     def __str__(self):
          return self.leave_type.short_title if self.leave_type else ''

class HRLeaveAllocation(CoreActionWithUpdate):
     employee                = models.ForeignKey(EmployeeDetails,on_delete=models.CASCADE, default=None, null=True, blank=True)
     leave                   = models.ForeignKey(HRLeaveMaster,on_delete=models.CASCADE, default=None, null=True, blank=True)
     fiscal_year             = models.ForeignKey(FiscalYear,on_delete=models.CASCADE, default=None, null=True, blank=True)
     opening_balance         = models.PositiveSmallIntegerField(default=0)
     allocated_days          = models.PositiveSmallIntegerField(default=0)
     availed_days            = models.PositiveSmallIntegerField(default=0)
     applied_days            = models.PositiveSmallIntegerField(default=0)
     adjust_days             = models.SmallIntegerField(default=0)
     created_at              = models.DateTimeField(auto_now_add=False, null=True, blank=True)

     class Meta:
          db_table            = 'hr_leave_allocations'
          verbose_name        = "Leave Allocation"
          verbose_name_plural = "Leave Allocations"

     def __str__(self):
          return (self.employee.personal.name if self.employee.personal_id else '') + ((" - " + self.leave.leave_type.short_title) if self.leave_id and self.leave.leave_type_id else '') + ((" - " + str(self.allocated_days)) if self.leave_id else '') + " day/s"

     @property
     def total_days(self):
          return int(self.allocated_days) + int(self.opening_balance) + int(self.adjust_days)

     @property
     def total_balance(self):
          return int(self.total_days) - int(self.availed_days) - int(self.applied_days)

class HRLeaveApplication(CoreActionWithUpdate):
     application_no          = models.CharField(max_length=100, unique=True)
     employee                = models.ForeignKey(EmployeeDetails,on_delete=models.CASCADE)
     leave                   = models.ForeignKey(HRLeaveType,on_delete=models.CASCADE)
     start_date              = models.DateField(auto_now=False, null=True, blank=True, default=None)
     end_date                = models.DateField(auto_now=False, null=True, blank=True, default=None)
     avail_place             = models.CharField(max_length=20, null=True, blank=True, default=None)
     reason                  = models.TextField(max_length=200, null=True, blank=True, default=None)
     is_post_approved        = models.BooleanField(default=False)
     attachment              = models.FileField(upload_to=upload_to("Leave-Applications"), null=True, blank=True, default=None)
     reporting_boss          = models.ForeignKey(Users, related_name="la_reporting_boss", on_delete=models.CASCADE, null=True, blank=True, default=None)
     reporting_boss_notes    = models.TextField(null=True, blank=True, default=None)
     reporting_boss_checked_at = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     dept_head               = models.ForeignKey(Users, related_name="la_dept_head", on_delete=models.CASCADE, null=True, blank=True)
     dept_head_notes         = models.TextField(null=True, blank=True, default='')
     dept_head_checked_at    = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     hr                      = models.ForeignKey(Users, related_name="la_hr", on_delete=models.CASCADE, null=True, blank=True)
     hr_notes                = models.TextField(null=True, blank=True, default='')
     hr_checked_at           = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     rejected_by             = models.ForeignKey(Users, related_name="la_rejected_by", on_delete=models.CASCADE, null=True, blank=True)
     reject_notes            = models.TextField(null=True, blank=True, default='')
     reject_at               = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)

     class Meta:
          db_table            = 'hr_leave_applications'
          verbose_name        = "Leave Application"
          verbose_name_plural = "Leave Applications"

     def __str__(self):
          return self.application_no

     @property
     def num_of_days(self):
          return int((self.end_date - self.start_date).days + 1) if self.end_date and self.start_date else 0

     def dept_heads(self) :
          return Users.objects.filter(department=self.created_by.department, 
               branch=self.created_by.branch, is_department_head=True)

     def allocation(self):
          current_fiscal_year = FiscalYear.objects.filter(status=Status.name('active')).order_by('-id').first()
          return HRLeaveAllocation.objects.filter(employee=self.employee, 
               leave__leave_type=self.leave, fiscal_year=current_fiscal_year).first()

     @property
     def leave_info(self):
          return self.leave.description if self.leave_id and self.leave.description else self.leave.short_title


class Attendance(CoreActionWithUpdate):
     employee                = models.ForeignKey(EmployeeDetails,on_delete=models.CASCADE, null=True, blank=True)
     shift                   = models.ForeignKey(Shift, related_name="attendance_shift", on_delete=models.CASCADE, null=True)
     location                = models.ForeignKey(Location, related_name="attendance_location", on_delete=models.CASCADE, null=True, blank=True)
     present_day             = models.DateField(auto_now=False, null=True, blank=True, default=None)
     in_time                 = models.TimeField(auto_now=False, null=True, blank=True, default=None)
     out_time                = models.TimeField(auto_now=False, null=True, blank=True, default=None)
     ot_hours                = models.PositiveIntegerField(default=0)
     ot_minutes              = models.PositiveIntegerField(default=0)
     outside_office          = models.BooleanField(default = False)

     class Meta:
          db_table            = 'hr_attendances'
          verbose_name        = "HR Attendance"
          verbose_name_plural = "HR Attendances"

     def __str__(self):
          return self.employee.personal.name if self.employee_id and self.employee.personal_id else "N/A"


     def save(self, *args, **kwargs):
          from datetime import datetime, date, time
          if self.employee.overtime and self.out_time :
               out_time = self.out_time if isinstance(self.out_time, time) else self.out_time.time()
               if self.shift_id and out_time and self.shift.end_time and (out_time > self.shift.end_time):
                    dateTimeA = datetime.combine(date.today(), out_time)
                    dateTimeB = datetime.combine(date.today(), self.shift.end_time)
                    time_difference = dateTimeA - dateTimeB
                    self.ot_hours = time_difference.total_seconds() / 3600
                    self.ot_minutes = time_difference.total_seconds() / 60
               else : self.ot_hours = self.ot_minutes = 0
          super(Attendance, self).save(*args, **kwargs)
          
     @property
     def work_hours(self):
          from datetime import datetime, timedelta
          time_diff = ''
          if self.out_time :
               dateTimeA = datetime.combine(datetime.today(), self.in_time)
               dateTimeB = datetime.combine(datetime.today(), self.out_time)
               if dateTimeB < dateTimeA : dateTimeB += timedelta(days=1)
               time_diff = dateTimeB - dateTimeA
               time_diff = time_diff if time_diff.total_seconds() > 60 else ""
          return time_diff
          
     @property
     def over_time(self):
          from datetime import time
          return (time(self.out_time) - time(self.employee.shift.end_time))
          
     @property
     def late_time(self):
          remark = ''
          from datetime import datetime, date
          if self.shift_id and self.shift.grace_time and self.in_time and (self.shift.grace_time < self.in_time) :
               dateTimeA   = datetime.combine(datetime.today(), self.in_time)
               dateTimeB   = datetime.combine(datetime.today(), self.shift.start_time)
               remark     += str(dateTimeA - dateTimeB)
          else : remark  += "00:00:00"
          return remark
          
     @property
     def early_leave_time(self):
          remark = ''
          from datetime import datetime, date
          if self.shift_id and self.shift.buffer_time and self.out_time and (self.shift.buffer_time > self.out_time) and date.today() != self.present_day :
               dateTimeA   = datetime.combine(datetime.today(), self.shift.end_time)
               dateTimeB   = datetime.combine(datetime.today(), self.out_time)
               remark     += str(dateTimeA - dateTimeB)
          else : remark = "00:00"
          return remark

     @property
     def work_hours_txt(self):
          return "<span class='text-warning font-weight-bold'> Work Hrs : " + str(self.work_hours) + " minutes</span><br/>" if self.work_hours != '' else ''
          
     @property
     def remark_text(self):
          remark = ''
          from datetime import date
          if self.shift_id and self.shift.grace_time and self.in_time and (self.shift.grace_time < self.in_time)  : remark = "Late"
          if self.shift_id and self.shift.buffer_time and self.out_time and date.today() != self.present_day and (self.shift.buffer_time > self.out_time)    : remark = "Early Out"
          if remark == '' : remark = "Present"
          return remark

     @property
     def remark_stext(self):
          remark = ''
          from datetime import date
          if self.shift_id and self.shift.grace_time and self.shift.buffer_time and self.in_time and self.out_time and (date.today() != self.present_day) and (self.shift.grace_time < self.in_time) and (self.shift.buffer_time > self.out_time) : remark  = "LE"
          elif self.shift_id and self.shift.buffer_time and self.out_time and (date.today() != self.present_day) and (self.shift.buffer_time > self.out_time) : remark  = "EO"
          elif self.shift_id and self.shift.grace_time and self.in_time and (self.shift.grace_time < self.in_time) : remark  = "LT"
          if remark == '' : remark = "PR"
          return remark

     @property
     def remarks(self):
          remark = ''
          from datetime import datetime, date
          if self.shift_id and self.shift.grace_time and self.in_time and (self.shift.grace_time < self.in_time) :
               remark   += "<span class='text-danger font-weight-bold'> Late : "
               dateTimeA = datetime.combine(datetime.today(), self.in_time)
               dateTimeB = datetime.combine(datetime.today(), self.shift.start_time)
               remark   += str(dateTimeA - dateTimeB) + " minutes</span><br/>"
          if self.shift_id and self.shift.buffer_time and self.out_time and (self.shift.buffer_time > self.out_time) and date.today() != self.present_day :
               remark   += "<span class='text-danger font-weight-bold'> Early Out : "
               dateTimeA = datetime.combine(datetime.today(), self.shift.end_time)
               dateTimeB = datetime.combine(datetime.today(), self.out_time)
               remark   += str(dateTimeA - dateTimeB) + " minutes</span><br/>"
          if remark == '' : remark = "<span class='text-success font-weight-bold'>Present</span>"
          return remark

class AttendanceDevice(CoreActionWithUpdate):
     device_id               = models.PositiveIntegerField(default=0)
     name                    = models.CharField(max_length=100)
     ip_address              = models.CharField(max_length=50)
     Mac                     = models.CharField(max_length=50, blank=True, null=True)
     Serial                  = models.CharField(max_length=50, blank=True, null=True)
     device_type             = models.CharField(max_length=50)
     location                = models.ForeignKey(Location, related_name="device_location", on_delete=models.CASCADE, blank=True, null=True)
     building                = models.ForeignKey(Building, related_name="device_bulding", on_delete=models.CASCADE, blank=True, null=True)
     floor                   = models.ForeignKey(HRFloor, related_name="device_floor", on_delete=models.CASCADE, blank=True, null=True)

     class Meta:
          db_table            = 'hr_attendance_devices'
          verbose_name        = "HR Attendance Device"
          verbose_name_plural = "HR Attendance Devices"

     def __str__(self):
          return self.name or "N/A"

class AttenddanceLog(CoreActionWithUpdate):
     attendance              = models.ForeignKey(Attendance,on_delete=models.CASCADE, null=True, blank=True, default=None)
     device                  = models.ForeignKey(AttendanceDevice,on_delete=models.CASCADE, null=True, blank=True, default=None)
     card_id                 = models.PositiveBigIntegerField(null=True, blank=True, default=None)
     punch_id                = models.PositiveBigIntegerField(null=True, blank=True, default=None)
     log_time                = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)

     class Meta:
          db_table            = 'hr_attendance_logs'
          verbose_name        = "HR Attendance Log"
          verbose_name_plural = "HR Attendance Logs"

     def __str__(self):
          return str(self.punch_id) or "N/A"

     def save(self, *args, **kwargs):
          employee, present_day = EmployeeDetails.objects.filter(punch_id=self.punch_id).last(), self.log_time.date()
          if employee:
               has_roaster_shift = HRShiftRoaster.objects.filter(employee=employee, roaster_date=present_day).first()
               shift = has_roaster_shift.shift if has_roaster_shift else employee.shift
               if shift.start_time and shift.end_time and shift.day_start and \
                    shift.start_time > shift.end_time and shift.day_start > self.log_time.time() : 
                    from datetime import timedelta
                    present_day -= timedelta(1)
               location = self.device.location if self.device_id else None
               if att := Attendance.objects.filter(employee=employee, shift=shift, present_day=present_day,
                    location=location, status=Status.name("Active")).first() : attendance = att
               else : attendance = Attendance.objects.create(employee=employee, shift=shift,
                    present_day=present_day, location=location, status=Status.name("Active"))
               if not attendance.in_time : attendance.in_time, attendance.created_by = self.log_time, self.created_by
               elif attendance.in_time and self.log_time.time() and attendance.in_time > self.log_time.time() :
                    if self.log_time.date() == present_day :
                         if not attendance.out_time : attendance.out_time = attendance.in_time
                         attendance.in_time = self.log_time
                    else :
                         from datetime import time
                         if not attendance.out_time or (time() < self.log_time.time()) or \
                              (attendance.out_time < self.log_time.time()) : attendance.out_time = self.log_time
               elif (not attendance.out_time and attendance.in_time != self.log_time.time()) \
                    or (attendance.out_time and attendance.out_time < self.log_time.time()) : 
                    attendance.out_time = self.log_time
               if attendance.created_by : attendance.updated_by = self.created_by
               attendance.save()
               self.attendance = attendance
               super(AttenddanceLog, self).save(*args, **kwargs)

class OutsideRemoteDuty(CoreActionWithUpdate):
     employee_id             = models.CharField(max_length=20, blank=True, null=True)
     date                    = models.DateField(auto_now=False, null=True, blank=True)
     in_time                 = models.TimeField(auto_now=False, null=True, blank=True, default=None)
     out_time                = models.TimeField(auto_now=False, null=True, blank=True, default=None)
     remarks                 = models.CharField(max_length=300, null=True, blank=True)
     reporting_boss          = models.ForeignKey(Users, related_name="ord_reporting_boss", on_delete=models.CASCADE, null=True, blank=True, default=None)
     reporting_boss_notes    = models.TextField(null=True, blank=True, default=None)
     reporting_boss_checked_at = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     
     class Meta:
          db_table            = 'hr_outside_remote_duty'
          verbose_name        = "HR Outside Remote Duty"
          verbose_name_plural = "HR Outside Remote Duties"

     def employee_name(self):
          return EmployeeInfo.objects.filter(employee_id=self.employee_id).last()


class EmployeeCalendar(models.Model):
     employee                = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
     calendar_day            = models.DateField(auto_now=False, null=True, blank=True, default=None)
     attendance              = models.ForeignKey(Attendance, on_delete=models.CASCADE, null=True, blank=True, default=None)
     absent                  = models.BooleanField(default=False)
     is_holiday              = models.BooleanField(default=False)
     is_weekend              = models.BooleanField(default=False)
     is_late                 = models.BooleanField(default=False)
     in_leave                = models.BooleanField(default=False)
     in_roaster              = models.BooleanField(default=False)
     outside_duty            = models.BooleanField(default=False)
     leave_application       = models.ForeignKey(HRLeaveApplication, on_delete=models.CASCADE, null=True, blank=True, default=None)
     created_at              = models.DateTimeField(auto_now_add=True)
     updated_at              = models.DateTimeField(auto_now=True)

     class Meta:
          db_table            = 'hr_employee_calendar'
          verbose_name        = "Employee Calendar"
          verbose_name_plural = "Employee Calendar"

     def __str__(self):
          return self.employee.personal.name + " - " + str(self.calendar_day.strftime("%d-%b-%Y")).upper()
     
     def day_status(self):
          status = ''
          if self.is_holiday      : status = "HL"
          elif self.in_roaster    : status = "RS"
          elif self.outside_duty  : status = "OS"
          elif self.is_weekend    : status = "WK"
          elif self.in_leave      : status = "LV"
          elif self.absent        : status = "AB"
          elif self.attendance_id : status = self.attendance.remark_stext
          return status
     
     def day_remarks(self):
          status = ''
          if self.is_holiday      : status = "Holiday"
          elif self.in_roaster    : status = "Roaster"
          elif self.outside_duty  : status = "Outside Duty"
          elif self.is_weekend    : status = "Weekend"
          elif self.in_leave      : status = "In Leave"
          elif self.absent        : status = "Absent"
          elif self.attendance_id : status = self.attendance.remark_text
          return status

     def remarks(self, check_date=None):
          remarks= ""
          if self.is_weekend and check_date:
               if str(check_date.weekday()) in self.employee.holiday + self.employee.branch.weekends : 
                    remarks += ' <span class="text-warning font-weight-bold">Weekend</span> <br />'
          if self.is_holiday and check_date:
               if str(check_date.weekday()) in self.employee.holiday + self.employee.branch.weekends : 
                    remarks += ' <span class="text-warning font-weight-bold">Weekend</span> <br />'
          if self.attendance: remarks += self.attendance.remarks
          if self.in_leave :
               remarks += ' <span class="text-warning font-weight-bold">' + self.leave_application.leave_info + '</span> <br />'
          elif self.absent : remarks += ' <span class="text-danger font-weight-bold">Absent</span> <br />'
          return remarks

class HRManPowerBudget(CoreActionWithUpdate): 
     branch                  = models.ForeignKey(Branch, on_delete=models.CASCADE,null=True, blank=True, default=None)
     budget_year             = models.PositiveSmallIntegerField(default=2022)
     department              = models.ForeignKey(Departments,on_delete=models.CASCADE, null=True, blank=True,)
     designation             = models.ForeignKey(Designations,on_delete=models.CASCADE, null=True, blank=True)
     manpower_limit_qty      = models.PositiveSmallIntegerField(null=True, blank=True, default=0)
     manpower_limit_value    = models.IntegerField(null=True, blank=True, default=0)
     ceo                     = models.ForeignKey(Users, related_name="ceo_mp_budget", on_delete=models.CASCADE, null=True, blank=True)
     ceo_action_at           = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     ceo_notes               = models.TextField(null=True, blank=True, default=None)
     md                      = models.ForeignKey(Users, related_name="md_mp_budget", on_delete=models.CASCADE, null=True, blank=True)
     md_action_at            = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     md_notes                = models.TextField(null=True, blank=True, default=None)

     class Meta:
          db_table            = 'hr_manpower_budget'
          verbose_name        = "HR ManPower Budget"
          verbose_name_plural = "HR ManPower Budgets"

class HREmployeeRecruitment(CoreActionWithUpdate): 
     name                    = models.CharField(max_length=100)
     branch                  = models.ForeignKey(Branch, on_delete=models.CASCADE,null=True, blank=True, default=None)
     recruit_year            = models.PositiveSmallIntegerField(default=2023)
     recruitment_types       = (('1', 'New'), ('2', 'Replacement'))
     recruitment_type        = models.CharField(max_length=100,choices=recruitment_types)
     department              = models.ForeignKey(Departments,on_delete=models.CASCADE, null=True, blank=True,)
     designation             = models.ForeignKey(Designations,on_delete=models.CASCADE, null=True, blank=True)
     replacement_of          = models.ForeignKey(EmployeeDetails, related_name="recruit_replacement_of", on_delete=models.CASCADE, null=True, blank=True)
     negotiated_salary       = models.IntegerField(null=True, blank=True, default=0)
     interviewr_comments     = models.TextField(null=True, blank=True, default=None)
     hr                      = models.ForeignKey(Users, related_name="recruit_hr", on_delete=models.CASCADE, null=True, blank=True)
     hr_action_at            = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     hr_comments             = models.TextField(null=True, blank=True, default=None)
     ceo                     = models.ForeignKey(Users, related_name="recruit_ceo_mp_budget", on_delete=models.CASCADE, null=True, blank=True)
     ceo_action_at           = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     ceo_notes               = models.TextField(null=True, blank=True, default=None)
     md                      = models.ForeignKey(Users, related_name="recruit_md_mp_budget", on_delete=models.CASCADE, null=True, blank=True)
     md_action_at            = models.DateTimeField(auto_now=False, null=True, blank=True, default=None)
     md_notes                = models.TextField(null=True, blank=True, default=None)
     skip_ceo_approval       = models.BooleanField(default=True)

     class Meta:
          db_table            = 'hr_employee_recruitments'
          verbose_name        = "HR Employee Recruitment"
          verbose_name_plural = "HR Employee Recruitments"

class HRSalaryCycle(CoreActionWithUpdate):
     branch              = models.ForeignKey(Branch, on_delete=models.CASCADE, default="")
     employee_category   = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="cycle_employee_category", null=True, blank=True, default=None)
     start_date          = models.IntegerField(blank=True,null=True)
     end_date            = models.IntegerField(blank=True,null=True)

     class Meta:
          db_table            = 'hr_salary_cycles'
          verbose_name        = "Salary Cycle"
          verbose_name_plural = "Salary Cycles"

     def __str__(self):
          return self.employee_category.value if self.employee_category_id else ''

class HRTiffinBillRule(CoreActionWithUpdate):
     name                = models.CharField(max_length=100)
     employee_category   = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name="tiffin_employee_category", null=True, blank=True, default=None)
     start_time          = models.TimeField(auto_now=False, null=True, blank=True, default=None)
     end_time            = models.TimeField(auto_now=False, null=True, blank=True, default=None)
     amount              = models.IntegerField(default=0)

     class Meta:
          db_table            = 'hr_tiffin_bill_rules'
          verbose_name        = "HR Tiffin Bill Rule"
          verbose_name_plural = "HR Tiffin Bill Rules"

     def __str__(self):
          return str(self.name) + " ( " + self.start_time.strftime("%I:%M %p") + " : " + self.end_time.strftime("%I:%M %p") + " ) - " + str(self.amount)

class HRAttendanceBonusRule(CoreActionWithUpdate):
     name                = models.CharField(max_length=100)
     max_late            = models.IntegerField(default=0)
     max_early_out       = models.IntegerField(default=0)
     max_absent          = models.IntegerField(default=0)
     amount              = models.IntegerField(default=0)

     class Meta:
          db_table            = 'hr_attendance_bonus_rules'
          verbose_name        = "HR Attendance Bonus Rule"
          verbose_name_plural = "HR Attendance Bonus Rules"

     def __str__(self):
          return str(self.name) + " - " + str(self.amount)
    

class HRShiftRoaster(CoreActionWithUpdate):
     employee            = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
     shift               = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True, null=True)
     roaster_date        = models.DateField(auto_now_add=False, null=True, blank=True)

     class Meta:
          db_table            = 'hr_shift_roasters'
          verbose_name        = "HR Shift Roaster"
          verbose_name_plural = "HR Shift Roasters"

     def __str__(self):
          return str(self.employee.name) + " - " + str(self.shift) + " - " + str(self.roaster_date)


class HRSalaryProcess(CoreActionWithUpdate):
     employees           = models.ManyToManyField(EmployeeDetails, related_name='employee_list', blank=True)
     month_list          = (
          ('1', 'January'),
          ('2', 'February'),
          ('3', 'March'),
          ('4', 'April'),
          ('5', 'May'),
          ('6', 'June'),
          ('7', 'July'),
          ('8', 'August'),
          ('9', 'September'),
          ('10', 'October'),
          ('11', 'November'),
          ('12', 'December'),
     )
     month               = models.CharField(max_length=15, choices=month_list, blank=True,null=True)
     year                = models.CharField(max_length=4, blank=True, null=True)
     submitted_at        = models.DateTimeField(auto_now=False, null=True, blank=True)
     notes               = models.TextField(null=True, blank=True, default='')
     recommend_by        = models.ForeignKey(Users, related_name='recommend_by', on_delete=models.CASCADE, null=True, blank=True)
     recommend_reject_date = models.DateTimeField(auto_now=False, null=True, blank=True)
     recommend_notes     = models.TextField(null=True, blank=True, default='')
     check_by            = models.ForeignKey(Users, related_name='check_by', on_delete=models.CASCADE, null=True, blank=True)
     check_reject_date   = models.DateTimeField(auto_now=False, null=True, blank=True)
     check_notes         = models.TextField(null=True, blank=True, default='')
     approve_by          = models.ForeignKey(Users, related_name='approve_by', on_delete=models.CASCADE, null=True, blank=True)
     approve_reject_date = models.DateTimeField(auto_now=False, null=True, blank=True)
     approve_notes       = models.TextField(null=True, blank=True, default='')
     acknowledge_by      = models.ForeignKey(Users, related_name='acknowledge_by', on_delete=models.CASCADE, null=True, blank=True)
     acknowledge_reject_date = models.DateTimeField(auto_now=False, null=True, blank=True)
     acknowledge_notes   = models.TextField(null=True, blank=True, default='')

     class Meta:
          db_table            = 'hr_salary_processes'
          verbose_name        = "HR Salary Process"
          verbose_name_plural = "HR Salary Processes"

class Loan(CoreActionWithUpdate):
     employee            = models.ForeignKey (EmployeeDetails, related_name='loans', on_delete=models.CASCADE, blank=True, null=True, default=None)
     purpose             = models.TextField(blank=True, null=True)
     amount              = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
     amount_paid         = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
     tenure_months       = models.PositiveIntegerField()
     monthly_installment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
     remarks             = models.TextField(blank=True, null=True)
     closed              = models.BooleanField(default = False)

     class Meta:
          db_table            = 'hr_loans'
          verbose_name        = "HR Loan"
          verbose_name_plural = "HR Loans"

     def __str__(self):
          return str(self.employee.name) + " - " + str(self.employee.employee_id)
     
     @property
     def remaining_loan_amount(self):
          return int(self.amount or 0) - int(self.amount_paid or 0)

class LoanRepayment(CoreActionWithUpdate):
     loan                = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
     payment_date        = models.DateField()
     amount_paid         = models.DecimalField(max_digits=10, decimal_places=2)
     remarks             = models.TextField(blank=True, null=True)

     class Meta:
          db_table            = 'hr_loan_repayments'
          verbose_name        = "HR Loan Repayment"
          verbose_name_plural = "HR Loan Repayments"

     def __str__(self):
          return str(self.loan.employee.name) + " - Loan #" + str(self.loan_id)
    

# Appraisal
class Appraisal(CoreActionWithUpdate):
     appraisee               = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE, related_name='appraisals')
     last_date_of_appraisal  = models.DateField(null=True, blank=True)
     last_increment_amount   = models.PositiveIntegerField(null=True, blank=True)
     self_justification      = models.TextField(null=True, blank=True)
     strengths               = models.TextField(null=True, blank=True)
     improvement_areas       = models.TextField(null=True, blank=True)
     grand_total             = models.PositiveIntegerField(null=True, blank=True)
     effective_from_date     = models.DateField(null=True, blank=True)
     promoted_as             = models.CharField(max_length=255, null=True, blank=True)
     increment_amount        = models.PositiveIntegerField(null=True, blank=True)
     promotion_recommendation= models.CharField(max_length=255, null=True, blank=True)
     recommendation_reason   = models.TextField(null=True, blank=True)
     coo_user                = models.ForeignKey('general.Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='coo_appraisals')
     coo_forwarded_at        = models.DateTimeField(null=True, blank=True)
     coo_comments            = models.TextField(null=True, blank=True)
     chairman_user           = models.ForeignKey('general.Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='chairman_appraisals')
     chairman_approved_at    = models.DateTimeField(null=True, blank=True)
     chairman_comments       = models.TextField(null=True, blank=True)

     class Meta:
          db_table            = 'hr_appraisals'
          verbose_name        = "HR Appraisal"
          verbose_name_plural = "HR Appraisals"

     def __str__(self):
          return f"Appraisal for {self.appraisee}"  

     def calculate_grand_total(self):
          """Calculate the grand total based on performance indicators."""
          indicators = self.performance_indicators.all()
          self.grand_total = sum(indicator.score for indicator in indicators)
          self.save()

class PerformanceIndicator(models.Model):
     appraisal               = models.ForeignKey(Appraisal, on_delete=models.CASCADE, related_name='performance_indicators')
     indicator_name          = models.CharField(max_length=255)
     score                   = models.PositiveSmallIntegerField()  # Range from 1-5

     class Meta:
          db_table            = "hr_appraisal_performance_indicators"
          verbose_name        = "HR Appraisal Performance Indicator"
          verbose_name_plural = "HR Appraisal Performance Indicators"

     def __str__(self):
          return f"{self.indicator_name}: {self.score}"

from django.utils import timezone
# cessation meaning the fact or process of ending or being brought to an end.
class EmployeeCessation(CoreActionWithUpdate):
     emolpoyee               = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE, related_name='cessation')
     effective_from_date     = models.DateField(null=True, blank=True)
     cessation_reason        = models.TextField(null=True, blank=True)
     reporting_to            = models.ForeignKey('general.Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='reporting_to_cessation')
     reporting_to_comments   = models.TextField(null=True, blank=True)
     hr_admin                = models.ForeignKey('general.Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_admin_cessation')
     hr_admin_approved_at    = models.DateTimeField(null=True, blank=True)
     hr_admin_comments       = models.TextField(null=True, blank=True)
     letter                  = models.FileField(upload_to="letter", max_length = 120, blank=True, null=True)
     letter_types            = (('1', 'Resignation'), ('2', 'Termination'))
     letter_type             = models.CharField(max_length=10,choices=letter_types)

     class Meta:
          db_table            = 'hr_cessation'
          verbose_name        = "HR Cessation"
          verbose_name_plural = "HR Cessations"
     
     def save(self, *args, **kwargs):
        today = timezone.now().date()
        if self.effective_from_date == today:
            if hasattr(self.emolpoyee, 'personal'):
                self.emolpoyee.personal.status = False
                self.emolpoyee.personal.save()
        super().save(*args, **kwargs)

     def __str__(self):
          return f"Cessation of {self.emolpoyee}"  
     