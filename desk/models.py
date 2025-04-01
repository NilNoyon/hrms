from django.db import models
from django.contrib.auth.models import AbstractUser
from general.models import *

class Issue(models.Model):
    ref             = models.CharField(max_length=15, null=True)
    fabric_order_no = models.CharField(max_length=55, null=True)
    taged_to        = models.ForeignKey(Users, on_delete=models.SET_NULL, blank=True, null=True,related_name='taged_to')  
    description     = models.TextField(null=True) #issue description
    attachment      = models.FileField(upload_to="helpdesk", max_length = 500, blank=True, null=True)
    issuer          = models.ForeignKey(Users, on_delete=models.SET_NULL, blank=True, null=True, related_name='issuer')  
    assigned_by     = models.IntegerField(blank=True, null=True) # manager
    assigned_to     = models.IntegerField(blank=True, null=True) # resolver
    priority        = models.IntegerField(default=1)
    assign_note     = models.CharField(max_length = 300, blank=True, null=True)
    resolver_note   = models.CharField(max_length = 1000, blank=True, null=True)
    feedback_note   = models.CharField(max_length = 1000, blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    assigned_at     = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    resolved_at     = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    canceled_by     = models.IntegerField(blank=True, null=True) # manager
    canceled_note   = models.CharField(max_length = 300, blank=True, null=True)
    canceled_at     = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    issue_statuses  = (
        ('1', 'Unassigned'),
        ('2', 'Assigned'),
        ('3', 'Running'),
        ('4', 'Solved'),
        ('5', 'Canceled'),
    )
    status          = models.CharField(default="1", max_length=50, choices=issue_statuses)
    da_status       = models.BooleanField(default = False)
    
    class Meta:
        db_table = 'hd_issue'
        verbose_name = "Issue"
        verbose_name_plural = "Issues"

    def __str__(self):
        return "#"+self.ref+"-"+str(self.description)[:30]

    def assigned_by_name(self):
        user = Users.objects.filter(id=self.assigned_by)
        if user:
            return user[0]
        else:
            return "N/A"

    def assigned_to_name(self):
        user = Users.objects.filter(id=self.assigned_to)
        if user:
            return user[0]
        else:
            return "N/A"

class AssessmentDeviceList(models.Model):
    device_name    = models.CharField(max_length=100, unique=True)
    status         = models.BooleanField(default = True)
    
    class Meta:
        db_table = 'hd_assessment_device_list'
        verbose_name = "Assessment Device"
        verbose_name_plural = "Assessment Device List"

    def __str__(self):
        return str(self.device_name)

class DeviceAssessments(models.Model):
    assessment_for     = models.ForeignKey(Users, on_delete=models.SET_NULL, blank=True, null=True) # issuer/user
    hd_issue           = models.ForeignKey(Issue, on_delete=models.SET_NULL, blank=True, null=True, default=None) # issue
    assessment_by      = models.IntegerField(blank=True, null=True) # resolver
    head_of_assessment = models.IntegerField(blank=True, null=True) # issuer/user department Head
    head_of_ict        = models.IntegerField(blank=True, null=True) # ICT department Head
    ed                 = models.IntegerField(blank=True, null=True) # ED 
    ceo                = models.IntegerField(blank=True, null=True) # CEO 
    canceled_by        = models.CharField(max_length = 100, blank=True, null=True)
    note               = models.CharField(max_length = 1500, blank=True, null=True)
    issuer_dpt_head_note = models.CharField(max_length = 150, blank=True, null=True)
    ict_head_note      = models.CharField(max_length = 300, blank=True, null=True)
    ed_note            = models.CharField(max_length = 150, blank=True, null=True)
    ceo_note           = models.CharField(max_length = 150, blank=True, null=True)
    canceled_note      = models.CharField(max_length = 300, blank=True, null=True)
    ict_finished_at    = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    canceled_at        = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    issuer_dpt_approve_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    ict_dpt_approve_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    ed_approve_at      = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    ceo_approve_at     = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    device_types = (
        ('New', 'New'),
        ('Replace', 'Replace'),
        ('Used', 'Used'),
        ('Handover', 'Handover'),
        ('Service', 'Service'),
    )
    device_type  = models.CharField(max_length=10, choices=device_types)
    device       = models.CharField(max_length=100, blank=True, null=True)
    item         = models.CharField(max_length=250, blank=True, null=True)
    question1    = models.BooleanField(default = False)
    question2    = models.BooleanField(default = False)
    question3    = models.BooleanField(default = False)
    statuses = (
        ('1', 'Pending Department Head Approval'),
        ('2', 'Pending ICT Department Head Approval'),
        # ('3', 'ED Approval'),
        ('4', 'Pending CEO Approval'),
        ('5', 'Approved'),
        ('6', 'Canceled'),
    )
    status       = models.CharField(default='1' ,max_length=2, choices=statuses)
    sr_status    = models.BooleanField(default = False)
    
    class Meta:
        db_table = 'hd_device_assessment'
        verbose_name = "Device Assessment"
        verbose_name_plural = "Device Assessments"

    def __str__(self):
        return str(self.assessment_for)

    def assessment_by_name(self):
        user = Users.objects.filter(id=self.assessment_by)
        if user:
            return user[0]
        else:
            return "N/A"

    def head_of_assessment_name(self):
        user = Users.objects.filter(id=self.head_of_assessment)
        if user:
            return user[0]
        else:
            return "N/A"

    def head_of_ict_name(self):
        user = Users.objects.filter(id=self.head_of_ict)
        if user:
            return user[0]
        else:
            return "N/A"

    def ceo_name(self):
        user = Users.objects.filter(id=self.ceo)
        if user:
            return user[0]
        else:
            return "N/A"

    def ed_name(self):
        user = Users.objects.filter(id=self.ed)
        if user:
            return user[0]
        else:
            return "N/A"

    def canceled_by_name(self):
        user = Users.objects.filter(id=self.canceled_by)
        if user:
            return user[0]
        else:
            return "N/A"
