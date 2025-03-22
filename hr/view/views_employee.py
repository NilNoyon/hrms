from datetime import time,datetime, timedelta
import hashlib, json, base64
from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from django.views.decorators.csrf import csrf_exempt
from general.models import CommonMaster, Company, Departments, Designations, Sections, Status, UserRoles, Users
from hr.models import Building, EmployeeInfo,EmployeeDetails,EmployeeNominee,EmployeeBankInfo,EmployeeEducation,EmployeeExperience, Shift, HRSalaryBreakdown, HRSalarySlabMaster, HRFloor, EmployeeUpdateRequest, Location, HRAttendanceBonusRule, GEOLocation, Division, SubSection
from hr.forms import EmployeeBankForm, EmployeeDetailsForm, EmployeeNomineeForm, ShiftForm, Pf_EmployeeForm
from django.urls import reverse, reverse_lazy
from django.db.models import Q,F, Value
from django.db.models.functions import Concat
from django.contrib import messages
from notification.signals import notify
from general.business_logic import approval_log_logic, common_logic
from django.core.files.base import ContentFile

ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()    

def get_employee_code(company):
    emp_details = EmployeeDetails.objects.filter(company_id=company.id).last()
    if emp_details and emp_details.personal.employee_id:
        splitted_id   = str(emp_details.personal.employee_id)[3:]
        emp_code = str("E") + str(int(splitted_id) + 1).rjust(6, '0')
    else: emp_code = str("E") + format(1, '06d')
    return emp_code

@csrf_exempt
def email_duplicate_check(request):
    chk_model   = request.POST.get('model')
    email       = request.POST.get('email').strip()
    if chk_model == "personal": duplicate = True if EmployeeInfo.objects.filter(email = email).count() > 0 else False
    if chk_model == "official": duplicate = True if EmployeeDetails.objects.filter(office_email = email, status=Status.name('active')).count() > 0 else False
    return JsonResponse(duplicate, safe=False)

@csrf_exempt
def employee_personal_info(request):
    first_name      = request.POST.get('first_name', '')
    first_name_bn   = request.POST.get('first_name_bn', '')
    phone_no        = request.POST.get('phone_no', 0)
    last_name       = request.POST.get('last_name', '')
    last_name_bn    = request.POST.get('last_name_bn', '')
    father_name     = request.POST.get('father_name', '')
    father_name_bn  = request.POST.get('father_name_bn', '')
    father_phone_no = request.POST.get('father_phone_no', 0)
    mother_name     = request.POST.get('mother_name', '')
    mother_name_bn  = request.POST.get('mother_name_bn', '')
    mother_phone_no = request.POST.get('mother_phone_no', 0)
    email           = request.POST.get('email', '')
    date_of_birth   = request.POST.get('date_of_birth', '')
    date_of_birth   = datetime.strptime(date_of_birth, "%d/%m/%Y").date() if date_of_birth  else None
    gender          = request.POST.get('gender', '')
    nationality     = request.POST.get('nationality', '')
    nid             = request.POST.get('nid', '')
    birth_certificate= request.POST.get('birth_certificate', '')
    passport        = request.POST.get('passport', '')
    religion        = request.POST.get('religion', None)
    if religion == 'null' : religion = None
    blood_group     = request.POST.get('blood_group', '')
    if blood_group == 'null' : blood_group = None
    maritial_status = request.POST.get('maritial_status', None)
    if maritial_status == 'null' : maritial_status = None
    spouse_name     = request.POST.get('spouse_name', '')
    spouse_name_bn  = request.POST.get('spouse_name_bn', '')
    spouse_phone_no = request.POST.get('spouse_phone_no', 0)
    no_of_children  = request.POST.get('no_of_children', 0)
    permanent_location = request.POST.get('permanent_location', '')
    permanent       = request.POST.get('permanent', '')
    permanent_bn    = request.POST.get('permanent_bn', '')
    present_location= request.POST.get('present_location', '')
    present         = request.POST.get('present', '')
    present_bn      = request.POST.get('present_bn', '')
    personal_id     = request.POST.get('personal_id', None)
    
    data={
        'first_name':first_name,'first_name_bn':first_name_bn,'last_name':last_name,'last_name_bn':last_name_bn,
        'phone_no':phone_no,'father_name':father_name,'father_name_bn':father_name_bn,'father_phone_no':father_phone_no,
        'mother_name':mother_name,'mother_name_bn':mother_name_bn,'mother_phone_no':mother_phone_no,'email':email,
        'date_of_birth': date_of_birth,'gender': gender if gender else None,'nationality':nationality,'nid':nid,
        'birth_certificate':birth_certificate,'passport':passport,'religion': religion if religion else None,
        'blood_group':blood_group,'marital_status': maritial_status if maritial_status else None,'spouse_name':spouse_name,
        'spouse_name_bn':spouse_name_bn,'spouse_phone_no':spouse_phone_no,'no_of_children':no_of_children,
        'permanent_location':permanent_location,'permanent_address':permanent,'present_location':present_location,
        "permanent_address_bn":permanent_bn, "present_address_bn":present_bn,'present_address':present,
        'created_by': request.session.get('id', None),'status': Status.name('Active')
    }
    if personal_id: 
        personal_info = EmployeeInfo.objects.filter(id=int(personal_id)).last()
        data["employee_id"] = personal_info.employee_id if personal_info and personal_info.employee_id else None
        emp_personal_form = Pf_EmployeeForm(data, instance=personal_info)
    else: emp_personal_form, personal_info = Pf_EmployeeForm(data), None
    if emp_personal_form.is_valid():
        personal    = emp_personal_form.save()
        photo       = request.FILES.get('photo', None)
        signature   = request.FILES.get('signature', None)
        
        if photo : 
            import os
            from PIL import Image
            if personal.photo and os.path.exists("/assets/uploads"+str(personal.photo)):
                os.remove("/assets/uploads"+str(personal.photo))
            if not os.path.exists(str(settings.MEDIA_ROOT)+'/employees/'):
                os.mkdir(str(settings.MEDIA_ROOT)+'/employees/')
            emp_photo = "/employees/" + str(request.session.get('employee_id'))+".png"
            size = 200, 200
            im = Image.open(photo).convert('RGB')
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(str(settings.MEDIA_ROOT)+emp_photo, format="PNG", quality=80)
            personal.photo = emp_photo
        if signature : 
            if personal.signature and os.path.exists("/assets/uploads"+str(personal.signature)):
                os.remove("/assets/uploads"+str(personal.signature))
            personal.signature = signature
        personal.save()
        personal_id, msg = personal.id, 'success'
    else:
        personal_id, msg = None, 'failed'
        for field in emp_personal_form:
            for error in field.errors:
                print(f"{field.name} : {error}")
    return JsonResponse({'msg':msg, 'personal_id':personal_id}, safe=False)

@csrf_exempt
def employee_official_info(request):
    personal_id     = request.POST.get('personal_id', None)
    official_id     = request.POST.get('official_id', None)
    personal        = EmployeeInfo.objects.filter(id=int(personal_id)).last()
    if not official_id: 
        emp_official = EmployeeDetails.objects.filter(employee_id=personal.employee_id).last()
    else : emp_official = EmployeeDetails.objects.filter(id=int(official_id)).last()
    company         = request.POST.get('company', None)
    location        = request.POST.get('location', None)
    department      = request.POST.get('department', None)
    designation     = request.POST.get('designation', None)
    division        = request.POST.get('division', None)
    sub_section     = request.POST.get('sub_section', None)
    section         = request.POST.get('section', None)
    floor           = request.POST.get('floor', None)
    line            = request.POST.get('line', None)
    unit            = request.POST.get('unit', None)
    cost_center     = request.POST.get('cost_center', None)
    shift           = request.POST.get('shift', None)
    reporting_to    = request.POST.get('reporting_to', None)
    office_mobile   = request.POST.get('office_mobile', 0)
    office_email    = request.POST.get('office_email', '')
    punch_id        = request.POST.get('punch_id', 0)
    employee_type   = request.POST.get('employee_type', None)
    skill_category  = request.POST.get('skill_category', None)
    attendance_bonus= request.POST.get('attendance_bonus', None)
    salary          = 0 # request.POST.get('salary', 0)
    pabx            = request.POST.get('pabx', '')
    grade           = request.POST.get('grade', '')
    joining_date    = request.POST.get('joining_date', '')
    confirmation_date = request.POST.get('confirmation_date', '')
    employee_category = request.POST.get('employee_category', None)
    provision_month = request.POST.get('provision_month', '')
    try             : provision_month = int(provision_month)
    except          : provision_month = ''
    employee_id     = request.POST.get('employee_id', '')
    tin             = request.POST.get('tin', '')
    building        = request.POST.get('building', None)
    transport_facility  = True if request.POST.get('transport_facility') == 'true' else False
    overtime            = True if request.POST.get('overtime') == 'true' else False
    off_day_ot          = True if request.POST.get('off_day_ot') == 'true' else False
    holiday_bonus       = True if request.POST.get('holiday_bonus') == 'true' else False
    income_tax          = True if request.POST.get('income_tax') == 'true' else False
    has_pf              = True if request.POST.get('has_pf') == 'true' else False
    is_user             = True if request.POST.get('is_user') == 'true' else False
    tiffin_bill         = True if request.POST.get('tiffin_bill') == 'true' else False
    status              = Status.name('Active') if request.POST.get('status') == 'true' else Status.name('Inactive')
    joining_date        = datetime.strptime(joining_date, "%d/%m/%Y").date() if joining_date else None
    confirmation_date   = datetime.strptime(confirmation_date, "%d/%m/%Y").date() if confirmation_date else None
    holiday             = None
    if company: 
        company = Company.objects.get(id=int(company))
        holiday = company.weekends
    holidays = request.POST.get('holiday', '')
    if holidays : holiday = json.loads(holidays)
    if reporting_to and not EmployeeDetails.objects.filter(id=int(reporting_to)).exists(): reporting_to = None 
    try             : skill_category = int(skill_category)
    except          : 
        if skill_category: skill_category, created = CommonMaster.objects.get_or_create(value_for=46, value=skill_category)
        else : skill_category = None
    data={'punch_id':punch_id, 'tin':tin, 'personal': personal_id, 'company':company.id, 'department': department, 'designation': designation, 'division': division, 'sub_section': sub_section, 'section': section, 'building': building, 'location':location, 'shift': shift, 'floor': floor,'cost_center': cost_center, 'unit': unit, 'line': line, 'office_mobile': office_mobile, 'pabx':pabx,'office_email': office_email, 'salary': salary, 'joining_date': joining_date, 'confirmation_date': confirmation_date,'has_pf': has_pf, 'initial_grade': grade, 'grade': grade, 'reporting_to': reporting_to,'employee_type': employee_type, 'employee_category': employee_category, 'skill_category': skill_category,'provision_month': provision_month, 'holiday': holiday, 'overtime': overtime, 'off_day_ot': off_day_ot,'income_tax' : income_tax, 'holiday_bonus': holiday_bonus, 'transport_facility': transport_facility,'created_by': request.session.get('id', None), 'status': status, 'attendance_bonus':attendance_bonus, 'tiffin_bill':tiffin_bill}
    if emp_official: 
        if EmployeeDetails.objects.filter(employee_id=employee_id).exclude(id=emp_official.id).exists():
            return JsonResponse({'msg':"Employee ID Already Exists!", 'official_id':official_id}, safe=False)
        data['salary'] = emp_official.salary
        emp_official_form = EmployeeDetailsForm(data, instance=emp_official)
    else: 
        if EmployeeDetails.objects.filter(employee_id=employee_id).exists():
            return JsonResponse({'msg':"Employee ID Already Exists!", 'official_id':official_id}, safe=False)
        emp_official_form = EmployeeDetailsForm(data)
    if emp_official_form.is_valid():
        personal = EmployeeInfo.objects.filter(id=int(personal_id)).last()
        personal.employee_id = employee_id
        personal.save()
        official = emp_official_form.save()
        official.employee_id = personal.employee_id
        official.save()
        official_id, msg = official.id, 'success'
        if official and is_user:
            md5_obj = hashlib.md5(str(personal.employee_id).encode())
            encripted_pass, report_to = md5_obj.hexdigest(), None
            user = Users.objects.filter(employee_id = official.personal.employee_id).last()
            if official.reporting_to: report_to = Users.objects.filter(employee_id = official.reporting_to.personal.employee_id).first()
            report_to = report_to.id if report_to else None
            if not user:
                user_role = UserRoles.objects.filter(name = 'User').first()
                if not user_role: user_role = UserRoles.objects.create(name = 'User')
                try: Users.objects.create(company_id = official.company_id, department_id = official.department_id, designation_id = official.designation_id, password = encripted_pass, password_text = official.personal.employee_id, email = official.office_email, reporting_to_id = report_to, employee_id = official.personal.employee_id.strip(), name = official.personal.name, role_id = user_role.id, status = 1)  
                except: pass
            else: 
                user.designation_id = official.designation_id
                user.name = official.personal.name
                user.email = official.office_email
                user.status = 1
                user.save()
            personal.status = True
            personal.employee_status = Status.name('Active')
            personal.save()
        elif official : Users.objects.filter(employee_id = official.personal.employee_id).update(status=0)
    else:
        official_id, msg = None, 'failed'
        for field in emp_official_form:
            for error in field.errors:
                print(f"{field.name} : {error}")
    return JsonResponse({'msg':msg, 'official_id':official_id}, safe=False)

@csrf_exempt
def employee_nominee_info(request):
    comparison_data, old_data, msg = {}, {}, ''
    employee = get_object_or_404(EmployeeInfo, id=request.POST.get('personal_id', 0))
    if request.POST.get('create', None) == 'true' : 
        nominee_data = create_nominee_info(request, employee)
        return JsonResponse(nominee_data, safe=False)
    data={
        'nominee_name'  : request.POST.get('nominee_name', '') or None,
        'nominee_nid'   : request.POST.get('nominee_nid', '') or None,
        'nominee_mobile': request.POST.get('nominee_mobile', '') or None,
        'relation'      : request.POST.get('relation', '') or None,
        'share_of_right': request.POST.get('share_of_right', '') or None,
        'nominee_address': request.POST.get('nominee_address', '') or None,
    }
    if nominee_id := request.POST.get('nominee_id', None): 
        old_data = EmployeeNominee.objects.filter(id=int(nominee_id)).values().last()
        if nominee_photo := request.FILES.get('nominee_photo') :
            nominee = EmployeeNominee.objects.filter(id=int(nominee_id)).last()
            if nominee.nominee_photo: nominee.nominee_photo.delete()
            nominee.nominee_photo   = nominee_photo
            nominee.save()
    for key, value in data.items():
        if old_data.get(key) != value:
            comparison_data[key] = {
                'old': old_data.get(key),
                'new': value
            }
    instance, created = EmployeeUpdateRequest.objects.get_or_create(employee=employee, model_object='EmployeeNominee', status=Status.name('Active'))
    if created :
        instance.created_by = get_object_or_404(Users, id=request.session.get('id', None))
        instance.data       = json.dumps(comparison_data)
        instance.save()
        msg, status = "Employee Information Submitted for Review!", 'success'

        # send notification
        n_sender        = instance.created_by
        n_recipient     = Users.objects.filter(Q(role__name__iexact="hr")|Q(secondary_role__contains=['HR']))
        n_action_url    = reverse('hr:update_requests')
        n_model         = 'EmployeeUpdateRequest'
        n_verb          = 'Update Request Submitted'
        n_description   = "1 new Update Request Submitted in HR"
        notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                    description=n_description, is_repeated=True)

    else : msg, status = "Already Request exist for EmployeeNominee against this Employee!", 'warning'
    return JsonResponse({'msg':msg, 'status':status}, safe=False)

def create_nominee_info(request, employee):
    employee = EmployeeDetails.objects.filter(employee_id=employee.employee_id).first()
    data={
        'nominee_name': request.POST.get('nominee_name', ''),
        'nominee_nid': request.POST.get('nominee_nid', ''),
        'nominee_mobile': request.POST.get('nominee_mobile', ''),
        'employee': employee, 'relation': request.POST.get('relation', ''),
        'nominee_address': request.POST.get('nominee_address', ''),
        'share_of_right': request.POST.get('share_of_right', ''),
        'created_by': request.session.get('id', None),
        'status': Status.name('Active'),
    }

    emp_nominee_form = EmployeeNomineeForm(data)
    if data['nominee_name'] and data['nominee_nid'] and data['share_of_right'] and emp_nominee_form.is_valid():
        nominee = emp_nominee_form.save()
        if nominee_photo := request.FILES.get('nominee_photo') :
            if nominee.nominee_photo: nominee.nominee_photo.delete()
            nominee.nominee_photo   = nominee_photo
        nominee.save()
        nominee_id, msg = nominee.id, 'success'
    else:
        nominee_id, msg = None, 'failed'
        ebs_bl_common.form_error_print(request, emp_nominee_form)
    return {'msg':msg,'nominee_id':nominee_id}

@csrf_exempt
def employee_bank_info(request):
    comparison_data, old_data, msg = {}, {}, ''
    employee = get_object_or_404(EmployeeInfo, id=request.POST.get('personal_id', 0))
    if request.POST.get('create', None) == 'true' : 
        bank_data = create_bank_info(request, employee)
        return JsonResponse(bank_data, safe=False)
    data={
        'bank_name'     : request.POST.get('bank_name', None) or None, 
        'branch_name'   : request.POST.get('branch_name', None) or None,
        'account_no'    : request.POST.get('account_no', None) or None,
    }
    if bank_id := request.POST.get('bank_id', None): old_data = EmployeeBankInfo.objects.filter(id=int(bank_id)).values().last()
    for key, value in data.items():
        if old_data.get(key) != value:
            comparison_data[key] = {
                'old': old_data.get(key),
                'new': value
            }
    instance, created = EmployeeUpdateRequest.objects.get_or_create(employee=employee, model_object='EmployeeBankInfo', status=Status.name('Active'))
    if created :
        instance.created_by = get_object_or_404(Users, id=request.session.get('id', None))
        instance.data       = json.dumps(comparison_data)
        instance.save()
        msg, status = "Employee Information Submitted for Review!", 'success'
        # send notification
        n_sender        = instance.created_by
        n_recipient     = Users.objects.filter(Q(role__name__iexact="hr")|Q(secondary_role__contains=['HR']))
        n_action_url    = reverse('hr:update_requests')
        n_model         = 'EmployeeUpdateRequest'
        n_verb          = 'Update Request Submitted'
        n_description   = "1 new Update Request Submitted in HR"
        notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                    description=n_description, is_repeated=True)
    else : msg, status = "Already Request exist for EmployeeBankInfo against this Employee!", 'warning'
    return JsonResponse({'msg':msg, 'status':status}, safe=False)

def create_bank_info(request, employee=None):
    employee = EmployeeDetails.objects.filter(employee_id=employee.employee_id).first()
    data={
        'bank_name': request.POST.get('bank_name', ''),
        'branch_name': request.POST.get('branch_name', ''),
        'account_no': request.POST.get('account_no', ''),
        'employee': employee, 'status': Status.name('Active'),
        'created_by': request.session.get('id', None),
    }
    emp_bank_form = EmployeeBankForm(data)
    if (data['bank_name'] or data['branch_name'] or data['account_no']) and emp_bank_form.is_valid():
        bank = emp_bank_form.save()
        bank_id, msg = bank.id, 'success'
    else:
        bank_id, msg = None, 'failed'
        ebs_bl_common.form_error_print(request, emp_bank_form)
    return {'msg':msg, 'bank_id':bank_id}

@csrf_exempt
def get_department_wise_section(request):
    id = request.POST.get('id')
    section_list = list(Sections.objects.filter(department_id=id).annotate(text=F('name')).values('id','text'))
    section_list.insert(0, {'id':'','text':''})
    return JsonResponse({'section':section_list}, safe=False)

@csrf_exempt
def get_company_wise_floor(request):
    id = request.POST.get('id')
    floor_list = list(Floor.objects.filter(company_id=id).annotate(text=F('name')).values('id','text'))
    floor_list.insert(0, {'id':'','text':''})
    return JsonResponse({'floor':floor_list}, safe=False)

@csrf_exempt
def get_company_wise_holidays(request):
    id = request.POST.get('id')
    company = Company.objects.filter(id=id).first()
    return JsonResponse({'holidays':company.weekends}, safe=False)

@csrf_exempt
def get_building_wise_hrfloor(request):
    floor_list = list(HRFloor.objects.filter(building_id=request.POST.get('id', 0)).annotate(text=F('name')).values('id','text'))
    floor_list.insert(0, {'id':'','text':''})
    return JsonResponse({'floor':floor_list}, safe=False)

@csrf_exempt
def get_company_and_floor_wise_line(request):
    company_id = request.POST.get('company_id')
    floor_id = request.POST.get('floor_id')
    line_list = list(SewingLine.objects.filter(company_id=company_id,floor_id=floor_id).annotate(text=F('name')).values('id','text'))
    line_list.insert(0, {'id':'','text':''})
    return JsonResponse({'line':line_list}, safe=False)

@csrf_exempt
def get_company_wise_line(request):
    company_id = request.POST.get('company_id')
    line_list = list(SewingLine.objects.filter(company_id=company_id).annotate(
                    text=Concat('floor__name',Value(' - '),'name')).values('id','text'))
    line_list.insert(0, {'id':'','text':''})
    return JsonResponse({'line':line_list}, safe=False)

@csrf_exempt
def get_all_shift(request):
    shift_list = list(Shift.objects.filter(status=Status.name('active')).distinct('shift_id').annotate(text=F('name')).values('id','text'))
    shift_list.insert(0, {'id':'','text':''})
    return JsonResponse({'shift':shift_list}, safe=False)


@csrf_exempt
def get_company_and_location_wise_shift(request):
    company_id = request.POST.get('company_id')
    location_id = request.POST.get('location_id')
    shift_list = list(Shift.objects.filter(company_id=company_id,location_id=location_id).annotate(text=F('name')).values('id','text'))
    shift_list.insert(0, {'id':'','text':''})
    return JsonResponse({'shift':shift_list}, safe=False)

@csrf_exempt
def get_company_and_location_wise_building(request):
    building_list = list(Building.objects.filter(location_id=request.POST.get('location_id', 0)).annotate(text=F('name')).values('id','text'))
    building_list.insert(0, {'id':'','text':''})
    return JsonResponse({'building':building_list}, safe=False)

@login
def employee_edit(request, id):
    personal= EmployeeInfo.objects.filter(id=id).last()
    office  = EmployeeDetails.objects.filter(personal=personal).order_by('-id').first()
    if office :
        nominee = EmployeeNominee.objects.filter(employee_id=office.id).order_by('-id').first()
        bank    = EmployeeBankInfo.objects.filter(employee_id=office.id).order_by('-id').first()
    else : nominee = bank = None
    user    = Users.objects.filter(employee_id=personal.employee_id).order_by('-id').first() if personal.employee_id else None
    template_name = "hr/employee/edit.html"
    search_roles, company_query = {"Admin", "Management"}, Q(status=True)
    if not search_roles.intersection(request.session.get("user_roles")):
        company_query &= Q(id__in=request.session.get("company_id_list"))
    context = {
        'personal':personal,
        'office':office,
        'bank':bank,
        'nominee':nominee,
        'is_user': user.status if user else False,
        'company_list'      : Company.objects.filter(company_query).order_by('short_name'),
        'location_list'     : Location.objects.filter(status=Status.name("Active")),
        'division_list'     : Division.objects.filter(status=Status.name("Active")).order_by('name'),
        'department_list'   : Departments.objects.filter(status=True).order_by('short_name', 'name'),
        'designation_list'  : Designations.objects.filter(status=True).order_by('name'),
        'shift_list'        : Shift.objects.filter(status=Status.name('active')),
        'employee_type_list':CommonMaster.objects.filter(value_for=4, status=True),
        'employee_category_list':CommonMaster.objects.filter(value_for=5, status=True),
        'marital_status_list': CommonMaster.objects.filter(value_for=6, status=True),
        'skill_category_list': CommonMaster.objects.filter(value_for=8, status=True),
        'gender_list'       : CommonMaster.objects.filter(value_for=7, status=True),
        'unit_list'         : CommonMaster.objects.filter(value_for=44, status=True),
        'religion_list'     : CommonMaster.objects.filter(value_for=3, status=True),
        'provision_month'   : EmployeeDetails.provision_months,
        'blood_group_list'  : EmployeeInfo.group_type,
        'ab_rule_list'      : HRAttendanceBonusRule.objects.filter(status=Status.name('Active')),
        'geo_location_list' : GEOLocation.objects.order_by('division_en', 'district_en', 'thana_en', 'post_office_en'),
    }
    return render(request, template_name, context)
    
    
@csrf_exempt
def get_employee_for_datatable(request):
    query, start, counter = Q(), request.POST.get('start', 0), request.POST.get('counter', 0)
    content, reset_data, end = '', False, int(start) + int(counter)

    if company := request.POST.get('company', None) : query &= Q(company_id=company)
    else :
        search_roles = {"Admin", "Management"}
        if not search_roles.intersection(request.session.get("user_roles")):
            query &= Q(company_id__in=request.session.get("company_id_list"))
    if department  := request.POST.get('department', None)  : query &= Q(department_id=department)
    if designation := request.POST.get('designation', None) : query &= Q(designation_id=designation)
    if employee_category := request.POST.get('employee_category', None) : query &= Q(employee_category_id=employee_category)

    start_date, end_date = request.POST.get('start_date', ''), request.POST.get('end_date', '')
    if start_date and end_date:
        start_date= datetime.strptime(start_date, "%Y-%m-%d")
        end_date  = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query     &= Q(joining_date__gte=start_date, joining_date__lte=end_date)

    if search_text := request.POST.get('search', None) :
        search_text = search_text.strip()
        query   &= Q(Q(personal__employee_id__icontains=search_text)|
                    Q(personal__first_name__icontains=search_text)|
                    Q(personal__last_name__icontains=search_text))
    employee_list       = EmployeeDetails.objects.filter(query).order_by("-id").distinct()
    total_data, content = employee_list.count(), ""
    if total_data == 0  : 
        content, reset_data = "<tr><td class='font-weight-bold' colspan='10'>No Data Found!</td></tr>", True
    else :
        for i in employee_list[int(start):int(end)]:
            employee_id     = i.personal.employee_id
            name            = i.personal.name
            company         = i.company.short_name if i.company else "N/A"
            designation     = i.designation.name if i.designation else "N/A"
            joining_date    = i.joining_date.strftime("%d-%b-%Y").upper() if i.joining_date else ""
            division        = i.division.name if i.division else "N/A"
            sub_section     = i.sub_section.name if i.sub_section else "N/A"
            unit            = i.unit.value if i.unit else "N/A"
            department      = i.department.title if i.department else "N/A"
            section         = i.section.name if i.section else "N/A"
            employee_category = i.employee_category.value if i.employee_category else "N/A"
            office_mobile   = i.office_mobile or "N/A"
            status = "checked" if i.status_id and i.status.title.lower() == "active" else ""
            status = """<div class="form-group mb-0">
                            <label class="">
                                <input type="checkbox" name="status" id="status-""" + str(i.id) + """" class="js-switch employee-update-switch" 
                                    data-id=""" + str(i.id) + """ data-color="#009efb" data-size="mini" """ + status + """ />
                            </label>
                        </div>"""
            edit_url        = reverse('hr:employee_edit', kwargs={'id': i.personal_id})
            view_url        = reverse('hr:employee_view', kwargs={'employee_id': i.personal_id})
            action          = ebs_bl_common.action_html(action_url=edit_url, color_text='text-success', icon='ti-pencil-alt', title_text='Edit Employee')
            action         += ebs_bl_common.action_html(action_url=view_url, color_text='text-info m-r-10', icon='icon-eye', title_text='View Employee')
            data = [employee_id, name, company, designation, joining_date, division, sub_section, unit, department, section, employee_category, office_mobile, status, action]
            content += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
    
    if 'true' == request.POST.get('reset', 'false') : reset_data = True
    end_pagination = False if int(end) < int(total_data) else True
    return JsonResponse({ "content":content, "end_pagination":end_pagination, "reset_data":reset_data, "total_data":total_data})

@csrf_exempt
def get_incomplete_employees_for_datatable(request):
    query, start, counter = Q(employee_details=None), request.POST.get('start', 0), request.POST.get('counter', 0)
    content, reset_data, end = '', False, int(start) + int(counter)

    if name := request.POST.get('name', None) : 
        name = name.strip()
        query &= Q(Q(first_name__icontains=name)|Q(last_name__icontains=name)|Q(full_name=name))
    if email := request.POST.get('email', None) : query &= Q(email=email)
    if phone  := request.POST.get('phone', None)  : query &= Q(phone_no=phone)

    start_date, end_date = request.POST.get('start_date', ''), request.POST.get('end_date', '')
    if start_date and end_date:
        start_date= datetime.strptime(start_date, "%Y-%m-%d")
        end_date  = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query     &= Q(date_of_birth__gte=start_date, date_of_birth__lte=end_date)

    employee_list       = EmployeeInfo.objects.annotate(full_name = Concat('first_name',Value(' '),'last_name')
                                ).filter(query).order_by("-id").distinct()
    total_data, content = employee_list.count(), ""
    if total_data == 0  : 
        content, reset_data = "<tr><td class='font-weight-bold' colspan='10'>No Data Found!</td></tr>", True
    else :
        for i in employee_list[int(start):int(end)]:
            mobile          = i.phone_no or "N/A"
            email           = i.email or "N/A"
            nid             = i.nid or "N/A"
            gender          = i.gender.value if i.gender_id else "N/A"
            created_by      = ebs_bl_common.user_html(i.created_by, 15)
            created_at      = i.created_at.strftime("%d-%b-%Y %I:%M %p").upper() if i.created_at else ""
            date_of_birth    = i.date_of_birth.strftime("%d-%b-%Y").upper() if i.date_of_birth else ""
            status = "checked" if i.employee_status_id and i.employee_status.title.lower() == "active" else ""
            status = """<div class="form-group mb-0">
                            <label class="">
                                <input type="checkbox" name="status" id="status-""" + str(i.id) + """" class="js-switch employeeinfo-update-switch" 
                                    data-id=""" + str(i.id) + """ data-color="#009efb" data-size="mini" """ + status + """ />
                            </label>
                        </div>"""
            edit_url        = reverse('hr:employee_edit', kwargs={'id': i.id})
            view_url        = reverse('hr:employee_view', kwargs={'employee_id': i.id})
            action          = ebs_bl_common.action_html(action_url=edit_url, color_text='text-success', icon='ti-pencil-alt', title_text='Edit Employee')
            action         += ebs_bl_common.action_html(action_url=view_url, color_text='text-info m-r-10', icon='icon-eye', title_text='View Employee')
            data = [i.name, i.father_name, date_of_birth, gender, nid, mobile, email, status, action]
            content += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
    
    if 'true' == request.POST.get('reset', 'false') : reset_data = True
    end_pagination = False if int(end) < int(total_data) else True
    return JsonResponse({ "content":content, "end_pagination":end_pagination, "reset_data":reset_data, "total_data":total_data})

@csrf_exempt
def employee_update_status(request):
    instance = get_object_or_404(EmployeeDetails, id=request.POST.get('id', 0))
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return JsonResponse({'status':instance.status.title.lower()})

@csrf_exempt
def employee_info_update_status(request):
    instance = get_object_or_404(EmployeeInfo, id=request.POST.get('id', 0))
    instance.employee_status = Status.name('Active') if instance.employee_status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return JsonResponse({'status':instance.employee_status.title.lower()})

@login
def employee_view(request, employee_id=None):
    template_name = "hr/employee/view.html"
    employee    = EmployeeInfo.objects.get(id=employee_id)
    details     = EmployeeDetails.objects.filter(personal=employee).last()
    # salary_breakdown = HRSalaryBreakdown.objects.filter(employee_id=details.id)
    context     = {'employee':employee, 'details':details}
    return render(request, template_name, context)

@csrf_exempt
def get_employees(request):
    query, employees = Q(status=Status.name("Active")), [{'id':"", "text":""}]
    if floor_id         := request.POST.get('floor_id', 0)      : query &= Q(floor_id=floor_id)
    elif building_id    := request.POST.get('building_id', 0)   : query &= Q(building_id=building_id)
    elif location_id    := request.POST.get('location_id', 0)   : query &= Q(location_id=location_id)
    elif company_id     := request.POST.get('company_id', 0)    : query &= Q(company_id=company_id)
    employees += [{'id':e.punch_id, 'text':e.personal.name + " - " + e.personal.employee_id} for e in EmployeeDetails.objects.filter(query)]
    return JsonResponse({'employees':employees}, safe=False)

@login
def update_requests(request):
    template_name = "hr/employee/requests.html"
    requests    = EmployeeUpdateRequest.objects.filter(status=Status.name("Active"))
    context     = {'requests':requests}
    return render(request, template_name, context)

@csrf_exempt
def get_update_requests_for_dataTable(request):
    query, data_list = Q(status=Status.name("Active")), []
    start   = int(request.POST.get('start', 0))
    if search_text:= request.POST.get('search[value]', ''):
        search_text = search_text.strip()
        query &= (Q(employee__first_name__icontains=search_text) 
            | Q(employee__last_name__icontains=search_text)
            | Q(employee__employee_id__icontains=search_text)
        )
    
    query_data_list = EmployeeUpdateRequest.objects.filter(query)  
    for r in query_data_list[start:start+20] :
        company     = r.employee.emp_details_info.company.short_name if r.employee.emp_details_info and r.employee.emp_details_info.company_id else ''
        department  = r.employee.emp_details_info.department.title if r.employee.emp_details_info and r.employee.emp_details_info.department_id else ''
        designation = r.employee.emp_details_info.designation.title if r.employee.emp_details_info and r.employee.emp_details_info.designation_id else ''
        created_by  = ebs_bl_common.user_html(r.created_by, 15)
        created_at  = str(r.created_at.strftime("%d-%b-%Y %I:%M %p").upper())
        action = '<a href="#infoModal" data-toggle="modal" data-id="'+str(r.id)+'" class="h4 m-r-10 text-success update_info"><span class="icon"><i class="ti-eye"></i></span></a>'
        data = [r.employee.employee_id, r.employee.name, company, department, designation, r.request_for, created_by, created_at, action]
        data_list.append(data)
        
    return JsonResponse(data_list, safe=False)


@csrf_exempt
def get_update_request_info(request):
    msg, html = '', ''
    request_id = request.POST.get('request_id', None)
    r = EmployeeUpdateRequest.objects.filter(id=request_id).first()
    if r: 
        data_dict = json.loads(r.data)
        html += "<input type='hidden' name='request_id' value='"+request_id+"'>"
        html += "<h3 class='text-center mb-3'>" + r.request_for + "</h3>"
        html += "<table class='table table-bordered'><tr><th>Data</th><th>Old</th><th>New</th></tr>"
        for key, data in data_dict.items():
            if key == 'employee_id' : 
                key = 'Employee'
                data['old'] = EmployeeInfo.objects.filter(id=data['old']).first()
                data['old'] = data['old'].name if data['old'] else ''
                data['new'] = EmployeeInfo.objects.filter(id=data['new']).first()
                data['new'] = data['new'].name if data['new'] else ''
            key = (" ".join(key.split("_"))).capitalize()
            html += "<tr><td>"+str(key)+"</td><td>"+str(data['old'] or '')+"</td><td>"+str(data['new'] or '')+"</td></tr>";
        html += "</table>"
    else : msg = 'No request found!'
    return JsonResponse({'msg':msg, 'html':html}, safe=False)


@csrf_exempt
def update_request_info(request):
    request_id = request.POST.get('request_id', None)
    r = EmployeeUpdateRequest.objects.filter(id=request_id).first()
    rstatus = request.POST.get('rstatus', None)
    if rstatus == 'update' : 
        data_dict   = json.loads(r.data)
        if r.model_object == 'EmployeeNominee':
            nominee_name    = data_dict['nominee_name']['new']      if 'nominee_name'       in data_dict else ''
            nominee_nid     = data_dict['nominee_nid']['new']       if 'nominee_nid'        in data_dict else ''
            relation        = data_dict['relation']['new']          if 'relation'           in data_dict else ''
            nominee_mobile  = data_dict['nominee_mobile']['new']    if 'nominee_mobile'     in data_dict else ''
            nominee_address = data_dict['nominee_address']['new']   if 'nominee_address'    in data_dict else ''
            share_of_right  = data_dict['share_of_right']['new']    if 'share_of_right'     in data_dict else ''
            if nominee := EmployeeNominee.objects.filter(employee__employee_id=r.employee.employee_id).last() :
                if nominee_name     : nominee.nominee_name      = nominee_name
                if nominee_nid      : nominee.nominee_nid       = nominee_nid
                if relation         : nominee.relation          = relation
                if nominee_mobile   : nominee.nominee_mobile    = nominee_mobile
                if nominee_address  : nominee.nominee_address   = nominee_address
                if share_of_right   : nominee.share_of_right    = share_of_right
                nominee.save()
            else : EmployeeNominee.objects.create(employee=r.employee.emp_details_info, nominee_name=nominee_name, 
                nominee_nid=nominee_nid, relation=relation, nominee_mobile=nominee_mobile, nominee_address=nominee_address, 
                share_of_right=share_of_right, created_by=r.created_by, status=Status.name("Active"))
        elif r.model_object == 'EmployeeBankInfo':
            bank_name   = data_dict['bank_name']['new']     if 'bank_name'      in data_dict else ''
            branch_name = data_dict['branch_name']['new']   if 'branch_name'    in data_dict else ''
            account_no  = data_dict['account_no']['new']    if 'account_no'     in data_dict else ''
            if bank := EmployeeBankInfo.objects.filter(employee__employee_id=r.employee.employee_id).last() :
                if bank_name    : bank.bank_name    = bank_name
                if branch_name  : bank.branch_name  = branch_name
                if account_no   : bank.account_no   = account_no
                bank.save()
            else : EmployeeBankInfo.objects.create(employee=r.employee.emp_details_info, bank_name=bank_name, 
                branch_name=branch_name, account_no=account_no, created_by=r.created_by, status=Status.name("Active"))
        r.status = Status.name('Updated')
    else : r.status = Status.name('Rejected')
    r.save()


    msg = "Successfully {}, update request for Employee - {}!".format(r.status.title, r.employee.employee_id)
    return JsonResponse({'msg':msg}, safe=False)