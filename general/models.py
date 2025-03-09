from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from django.utils.safestring import mark_safe
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class Status(models.Model):
    title                  = models.CharField(max_length=30)
    class Meta:
        db_table = 'status'
        verbose_name = "Status"
        verbose_name_plural = "Status" 
        
    def __str__(self):
        return str(self.id) + " - " + self.title

    @classmethod
    def name(self, name=""):
        if name:
            try:
                obj, created = self.objects.get_or_create(title=name.title())
                return obj
            except Status.DoesNotExist : return None
        else : return None


class Company(models.Model):
    name                = models.CharField(max_length = 100, unique=True)
    short_name          = models.CharField(max_length = 10, blank=True) #need to unique = true later
    address             = models.CharField(max_length = 100, blank=True)
    phone_no            = models.CharField(max_length = 15, blank=True)
    email               = models.EmailField(max_length = 80, blank=True)
    url                 = models.CharField(max_length = 20, blank=True)
    licence_no          = models.CharField(max_length = 50, blank=True)
    status              = models.BooleanField(default = True)

    class Meta:
        db_table = 'company'
        verbose_name = "Companies"
        verbose_name_plural = "Companies" 

    def __str__(self):
        return '%s' % (self.name)

class Branch(models.Model):
    name                = models.CharField(max_length = 100, unique=True)
    short_name          = models.CharField(max_length = 10, blank=True) #need to unique = true later
    address             = models.CharField(max_length = 100, blank=True)
    phone_no            = models.CharField(max_length = 15, blank=True)
    email               = models.EmailField(max_length = 80, blank=True)
    fax                 = models.CharField(max_length = 20, blank=True)
    licence_no          = models.CharField(max_length = 50, blank=True)
    branch_head         = models.ForeignKey("general.Users", related_name="unit_head", on_delete = models.SET_NULL, blank=True, null=True)  #this is the Branch Head PK from user table of this company    
    company             = models.ForeignKey(Company, related_name="company", on_delete = models.SET_NULL, blank=True, null=True)  #this is the Branch Head PK from user table of this company    
    status              = models.BooleanField(default = True)
    weekends            = ArrayField(models.CharField(max_length=100), null=True, blank=True, size=100) # Weekend day

    class Meta:
        db_table = 'branch'
        verbose_name = "Brnaches"
        verbose_name_plural = "Branches" 

    def __str__(self):
        return '%s' % (self.name)
    
class Designations(models.Model):
    name           = models.CharField(max_length = 200, unique=True)
    short_name     = models.CharField(max_length = 10)
    status         = models.BooleanField(default = True)

    class Meta:
        db_table = 'designations'
        verbose_name = "Designation"
        verbose_name_plural = "Designations" 

    def __str__(self):
        return '%s' % (self.name)
    
    @property
    def title(self):
        return self.short_name if self.short_name else self.name


class Departments(models.Model):
    name           = models.CharField(max_length=200, unique=True)
    short_name     = models.CharField(max_length=10, blank=True) #need to unique = true later
    status         = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'departments'
        verbose_name = "Department"
        verbose_name_plural = "departments" 

    def __str__(self):
        return '%s' % (self.name)

    @staticmethod
    def get_name_wise_last_department(department_text):
        department_query = Departments.objects.filter(name=department_text.strip())
        if department_query.exists(): department = department_query.last()
        else: department = None
        return department
    
    @property
    def title(self):
        return self.short_name if self.short_name else self.name
    
class UserRoles(models.Model):
    name           = models.CharField(max_length = 80, unique=True)
    status         = models.BooleanField(default = True)

    class Meta:
        db_table = 'user_roles'
        verbose_name = "Role"
        verbose_name_plural = "User Roles" 

    def __str__(self):
        return '%s' % (self.name)

class Users(models.Model):
    name               = models.CharField(max_length = 50)
    employee_id        = models.CharField(max_length = 15, unique=True)
    password           = models.CharField(max_length = 100)
    password_text      = models.CharField(max_length = 100)
    email              = models.EmailField(max_length = 100, blank=True, null=True)
    branch             = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    department         = models.ForeignKey(Departments, on_delete=models.SET_NULL, blank=True, null=True)
    designation        = models.ForeignKey(Designations, on_delete=models.SET_NULL, blank=True, null=True)
    reporting_to       = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)
    role               = models.ForeignKey(UserRoles, on_delete=models.SET_NULL, blank=True, null=True)
    secondary_role     = ArrayField(models.CharField(max_length=50, blank=True, null=True), null=True, blank=True, size=20) #This filed is used when user need to assign multi role
    secondary_company  = ArrayField(models.IntegerField(blank=True, null=True), null=True, blank=True, size=20) #This filed is used when user need to assign multiple company
    helpdesk_role      = models.IntegerField(default=1) #1 = Issuer, 2 = Resolver, 3 = Manager, 4 = Department Head
    is_department_head = models.BooleanField(default=False)
    status             = models.BooleanField(default=1)

    def __str__(self):
        return '%s' % (self.name)
    
    def official_info(self):
        from hr.models import EmployeeDetails
        user = EmployeeDetails.objects.filter(personal__employee_id=self.employee_id).first()
        return user.current_mobile if user else "N/A"
    
    def signature(self):
        from hr.models import EmployeeInfo
        emp = EmployeeInfo.objects.get(employee_id=self.employee_id)
        if emp.signature: signature = "<img style='height: 50px; width: auto; padding: 0px !important; margin: 0px !important;' src='"+settings.DOMAIN_URL+"assets"+emp.signature.url+"' alt='"+emp.name+"' align='middle' />"
        else: signature = "<p style='height: 50px; width: auto; padding: 0px !important; margin: 0px !important;'></p>"
        return mark_safe(signature)
    
    def dept_head(self):
        user = Users.objects.filter(department=self.department, company=self.company, is_department_head=True)
        return user.first() if user and user.first() else self.reporting_to
    
    def sc_head(self):
        from django.db.models import Q
        return Users.objects.filter(Q(role__name='SC Head')|Q(secondary_role__contains=['SC Head']))
    
    def sc_user_level(self):
        user_level = 0
        if self.role.name == "Procurer"                             : user_level = 1
        elif self.role.name == "SC Head"                            : user_level = 2
        elif self.role.name == "Audit"                              : user_level = 3
        elif 'management' in self.role.name.lower()                 : user_level = 6
        elif 'admin' in self.role.name.lower()                      : user_level = 7
        elif 'finance' in self.role.name.lower()                    : user_level = 8
        return user_level

    class Meta:
        db_table = 'users' 
        verbose_name = "User"
        verbose_name_plural = "Users" 

class CoreAction(models.Model):
    created_by = models.ForeignKey(Users, related_name="%(class)s_created_by", related_query_name="%(class)s_created_by", 
                                   on_delete=models.CASCADE, null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status     = models.ForeignKey(Status, on_delete=models.CASCADE, null=True, blank=True)

    class Meta: abstract = True


class CoreActionWithUpdate(CoreAction):
    updated_by = models.ForeignKey(Users, related_name="%(class)s_updated_by", related_query_name="%(class)s_updated_by", 
                                        on_delete=models.CASCADE, null=True, blank=True, default=None)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta: abstract = True

class MenuList(models.Model):
    menu_name   = models.CharField(max_length=50)
    menu_url    = models.CharField(max_length=90)
    module_types = (
        ('Administration', 'Administration'),
        ('HR', 'HR'),
        ('Fixed Asset', 'Fixed Asset'),
    )
    module_name      = models.CharField(max_length=50, choices=module_types)
    is_sub_menu      = models.BooleanField(default=False)
    sub_menu_name    = models.CharField(max_length=50,blank=True,null=True)
    menu_order       = models.IntegerField(default=0)
    menu_icon        = models.CharField(max_length=50,blank=True)
    status           = models.BooleanField(default=True)

    def __str__(self):
        return self.menu_name

    class Meta:
        db_table = 'menu_list'
        verbose_name = "Menu"
        verbose_name_plural = "Menu List" 

class UserPermission(models.Model):
    user            = models.ForeignKey(Users, on_delete = models.CASCADE) 
    menu            = models.ForeignKey(MenuList, on_delete = models.CASCADE)
    view_action     = models.BooleanField(default = False)      
    insert_action   = models.BooleanField(default = False)      
    update_action   = models.BooleanField(default = False)      
    delete_action   = models.BooleanField(default = False)   
    permission_date = models.DateTimeField(auto_now_add=True)
    permitted_by    = models.IntegerField(default=0) 
    status          = models.BooleanField(default=True)   
    
    def __str__(self):
        return str(self.user)   
        
    class Meta:
        db_table = 'user_permission'
        verbose_name = "User Permission"
        verbose_name_plural = "User Permissions"

class Bank(models.Model):
    name            = models.CharField(max_length=300, default='')
    short_name      = models.CharField(max_length=100, default='', blank=True, null=True)
    branch          = models.TextField(blank=True, default='')
    route_no        = models.CharField(max_length=50, blank=True, default='')
    swift_code      = models.CharField(max_length=100, blank=True, default='')
    is_foreign      = models.BooleanField(default=False)

    class Meta:
        db_table = 'banks'
        
    def __str__(self):
        return self.name+" ("+self.branch+")"

class ForgotPassword(models.Model):
    email          = models.EmailField(max_length = 100)
    token          = models.CharField(max_length = 100)
    created_at     = models.DateTimeField(auto_now_add=True)
    is_used        = models.BooleanField(default = False)

    class Meta:
        db_table            = 'forgot_password'
        verbose_name        = "User"
        verbose_name_plural = "Forgot Password" 

    def __str__(self):
        return '%s' % (self.email)

class CommonMaster(models.Model): #this common model/table will use for all small master tables
    value          = models.CharField(max_length=120)
    value_types = (
        ('1', 'Currency Type'), #this is use for Currency Type
        ('2', 'Payment Term'), #this is use for Payment Term
        ('3', 'Religion'),
        ('4', 'HR Employee Types'),
        ('5', 'HR Employee Categories'),
        ('6', 'Marital Status'),
        ('7', 'Gender'),
        ('8', 'HR Employee Skills'),
        ('9', 'Salary Heads'),
        
    )
    value_for      = models.CharField(max_length=50, choices=value_types)
    ordering       = models.IntegerField(default=0)
    created_at     = models.DateTimeField(auto_now_add=True)
    status         = models.BooleanField(default = True)

    class Meta:
        db_table = 'common_master'
        verbose_name = "Master"
        verbose_name_plural = "Common Master" 

    def __str__(self):
        return '%s' % (self.value)

    @classmethod
    def value_for_id(self, i=""):
        try : return self.objects.filter(value_for=i).order_by('ordering')
        except Status.DoesNotExist : return []

    @classmethod
    def name(self, name=''):
        try: return self.objects.get(value = name)
        except CommonMaster.DoesNotExist: return None

    @classmethod
    def get_or_create_name(self, name='', value_for=''):
        if name:
            try:
                obj, created = self.objects.get_or_create(value = name, value_for = value_for)
                return obj
            except CommonMaster.DoesNotExist : return None
        else : return None

    @staticmethod
    def get_name_wise_last_data(value, value_for):
        data_query = CommonMaster.objects.filter(value_for=value_for, status=True, value=value)
        if data_query.exists(): data = data_query.last()
        else: data = CommonMaster.objects.create(value_for=value_for, status=True, value=value)
        return data
    
    @property
    def conv_from_bdt(self):
        cc_obj  = CurrencyConversion.objects.filter(from_currency_id=self.id, to_currency__value__exact="BDT").first()
        return cc_obj.rate if cc_obj else 1



class Sections(CoreAction):
    department     = models.ForeignKey(Departments, on_delete=models.SET_NULL, blank=True, null=True)
    name           = models.CharField(max_length=100)

    class Meta:
        db_table = 'sections'
        verbose_name = "Section"
        verbose_name_plural = "Sections" 

    def __str__(self):
        return 'dept: {} ~ section: {}'.format(self.department.name, self.name)

class ApprovalLog(models.Model):
    model                   = models.CharField(max_length=50) # model name
    ref_id                  = models.BigIntegerField(default=0) # refernce primary key
    reference               = models.CharField(max_length=100) # place here the referece no or generated no/code such as item code FAB/0001 
    approved_rejected_by    = models.ForeignKey(Users, on_delete=models.CASCADE) 
    approved_rejected_date  = models.DateTimeField(auto_now_add=False, null=True, blank=True,)
    approved_rejected_note  = models.TextField(null=True,blank=True)
    status_message          = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, null=True, blank=True, default='')
    status                  = models.ForeignKey(Status, on_delete=models.CASCADE)

    class Meta:
        db_table = 'approval_log'

    def __str__(self):
        return self.reference

        
from django.contrib.sessions.models import Session
class CustomSession(models.Model):
    user                = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='users_session') 
    ip_address          = models.GenericIPAddressField(blank=True,null=True) #public/real ip of this network
    local_ip_address    = models.GenericIPAddressField(blank=True,null=True) #local or node ip address
    mac_address         = models.CharField(max_length=32,blank=True,null=True) 
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "custom_session"     
        
class CommonLogs(models.Model):
    content_type     = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='common_logs', default=None, blank=True, null=True)
    object_id        = models.IntegerField(default=None, blank=True, null=True)
    content_object   = GenericForeignKey( # this will be the model name of any model in this project
        'content_type',
        'object_id',
    ) 
    previous_status = models.CharField(max_length=64, null=True, blank=True, default='')
    status          = models.CharField(max_length=64, null=True, blank=True, default='')
    description     = models.TextField(max_length=1000, null=True, blank=True, default='')
    log_at          = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    ip_address      = models.GenericIPAddressField(null=True, blank=True) 
    log_by          = models.ForeignKey(Users, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name="common_logs")        
    
    class Meta:
        db_table = 'common_logs'
        ordering = ['-log_at']
        verbose_name = "Log"
        verbose_name_plural = "Common Logs"         


class UoM(models.Model):
    name                = models.CharField(max_length = 100, unique=True, db_index=True)
    short_name          = models.CharField(max_length = 5, unique=True, db_index=True)

    def save(self, *args, **kwargs):
        self.name           = self.name.title()
        self.short_name     = self.short_name.lower()
        super(UoM, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.short_name)

    class Meta:
        db_table                = 'item_uoms'
        verbose_name            = "Item - Unit Of Measurement"
        verbose_name_plural     = "Item - Unit Of Measurement"