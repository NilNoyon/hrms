from datetime import date, datetime, timedelta, time, timezone
import hashlib, os, pandas as pd, numpy as np, re
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.urls import reverse_lazy
from django.shortcuts import render
from PIL import Image
from general.decorators import login, permission
from django.conf import settings
from django.contrib import messages
from django.utils.text import Truncator
from general.models import *
from django.db.models import Q, F, Sum, Count
from dateutil import relativedelta
from django.views.decorators.csrf import csrf_exempt
from notification.signals import notify
from general.utils import render_to_pdf
from general.templatetags import general_filters
from hr.forms import *
from hr.models import EmployeeCessation, EmployeeInfo, EmployeeDetails, EmployeePF, EmployeePromotionDemotion, EmployeeTransfer,  PFDiscontinue, PFMonthlyContribution, PolicyMaster, PromotionDemotionHistory, ProvidentFundMaster, Holiday, HolidaySetup, NoticeBoard, HRLeaveType, HRLeaveMaster, HRLeaveAllocation, HRLeaveApplication, Attendance, AttenddanceLog, AttendanceDevice, HRFloor, HRSalarySlabMaster, HRIncomeTaxSlabMaster, HRSalaryBreakdown, HRMontlySalaryDetails, OutsideRemoteDuty, HRSalaryCycle, GEOLocation, HRSalaryProcess, HRShiftRoaster, HRAttendanceBonusRule, Shift, LoanRepayment, Division, SubSection, FiscalYear

def exclude_company(company_id):
    return Company.objects.exclude(id=company_id)

def str_from_xls(value, change_quote=True, date_field = False, time_field=False):
    value= str(value)
    value   = " ".join(value.split())
    if change_quote:
        value   = general_filters.strip_double_quotes(value) if value else ''
        value   = general_filters.strip_single_quote(value)  if value else '' 
    value = str(value) if str(value) not in ['nan', 'NaT'] else ''
    if date_field and value:
        try : value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
        except: 
            try : value = datetime.strptime(value, "%d-%m-%Y").date()
            except : 
                try : value = datetime.strptime(value, "%d/%m/%Y").date()
                except : value = None
    if time_field and value:
        try : value = datetime.strptime(value, "%H:%M:%S").time()
        except : 
            try : value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").time()
            except : value = None
    elif date_field and not value: value = None
    elif time_field and not value: value = None
    return value

def retrun_str_from_xls(value):
     if str(value) == 'nan': value = ''
     else:
          value = re.sub(' +', ' ', value)
          value = value.strip()
          value = general_filters.strip_double_quotes(value)
          value = general_filters.strip_single_quote(value)
          if (isinstance(value, float)): value = int(value)
     return str(value)

@login
def syncUsers(request):
     try:
          #for updating and creating new user from employee table
          employee_list = EmployeeInfo.objects.raw("SELECT * FROM hr_employeeinfo e where employee_id not in(select employee_id from public.users)")
          if len(employee_list) > 0:
               user_role, created = UserRoles.objects.get_or_create(name='User')
               for u in employee_list:
                    md5_obj = hashlib.md5(u.employee_id.encode())
                    encripted_pass = md5_obj.hexdigest() 
                    emp_details = u.employee_details.last()
                    if not Users.objects.filter(employee_id = u.employee_id) and emp_details:
                         report_to = None
                         if emp_details.reporting_to: report_to = Users.objects.filter(employee_id = emp_details.reporting_to.employee_id).last()
                         Users.objects.create(company_id = emp_details.company_id, department_id = emp_details.department_id, designation_id = emp_details.designation_id, password = encripted_pass, password_text = u.employee_id,
                              employee_id = u.employee_id.strip(), name = u.name, role_id = user_role.id, email = emp_details.office_email, reporting_to = report_to
                         )  
          
               #for updating department head of each employee and also update his department head and company data
               # for u in employee_list:
               #     report_to = Users.objects.filter(employee_id = u.report_to)
               #     company     = Company.objects.filter(short_name = u.company).first()
               #     if report_to: 
               #         Users.objects.filter(id = report_to[0].id).update(is_department_head = True)
               #         report_to = report_to[0].id
               #     else: report_to = None
               #     Users.objects.filter(employee_id = u.employee_id).update(reporting_to_id = report_to, company_id = company.id)
     except Exception as msg:
          messages.warning(request, str(msg))
          return redirect('hr:employee_add')

@login
def syncEmployees(request):
    # try:
        from desk.models import EmployeeInfo as desk_employee
        employee_list = desk_employee.objects.all()
        if employee_list:
            for counter, u in enumerate(employee_list):
                try:
                    company     = Company.objects.get(short_name = u.company)
                    department  = Departments.objects.get(name = u.department)
                    designation = Designations.objects.get(name = u.designation)
                    if not EmployeeInfo.objects.filter(employee_id = u.employee_id):
                        EmployeeInfo.objects.create(company_id = company.id, department_id = department.id, designation_id = designation.id,
                            employee_id = u.employee_id, name = u.name, photo = str(u.photo) if u.photo else "", signature = str(u.signature) if u.signature else "",
                            section = u.section, location = u.location, email = u.email, phone_no = u.phone, pabx = u.pabx, blood_group = u.blood_group, status = u.status
                        )  
                except Exception as msg:
                    continue
        
            # for updating department head of each employee and also update his department head and company data
            for u in employee_list.filter(report_to__isnull = False):
                try:
                    emp_head = EmployeeInfo.objects.filter(employee_id = u.report_to).first()
                    if emp_head: EmployeeInfo.objects.filter(employee_id = u.employee_id).update(reporting_to_id = emp_head.id)
                except Exception as msg:
                    continue
    # except Exception as msg:
    #     pass

@login
def employee_add(request):
    chk_permission   = permission(request,"/hr/employee-add/")
    if chk_permission and chk_permission.insert_action:
        search_roles, company_query = {"Admin","Super Admin", "Management"}, Q(status=True)
        if not search_roles.intersection(request.session.get("user_roles")):
            company_query &= Q(id=request.session.get("branch_id"))
        context = {
            'company_list'      : Branch.objects.filter(company_query).order_by('short_name'),
            'division_list'     : Division.objects.filter(status=Status.name('active')).order_by('name'),
            'department_list'   : Departments.objects.filter(status=True).order_by('short_name', 'name'),
            'designation_list'  : Designations.objects.filter(status=True).order_by('name'),
            'geo_location_list' : GEOLocation.objects.order_by('division_en', 'district_en', 'thana_en', 'post_office_en'),
            'shift_list'        : Shift.objects.filter(status=Status.name('active')),
            'employee_type_list':CommonMaster.objects.filter(value_for=4, status=True),
            'employee_category_list':CommonMaster.objects.filter(value_for=5, status=True),
            'marital_status_list': CommonMaster.objects.filter(value_for=6, status=True),
            'skill_category_list': CommonMaster.objects.filter(value_for=8, status=True),
            'gender_list'       : CommonMaster.objects.filter(value_for=7, status=True),
            'unit_list'         : CommonMaster.objects.filter(value_for=44, status=True),
            'religion_list'     : CommonMaster.objects.filter(value_for=3, status=True),
            'ab_rule_list'      : HRAttendanceBonusRule.objects.filter(status=Status.name('Active')),
            'provision_month'   : EmployeeDetails.provision_months, 'blood_group_list' : EmployeeInfo.group_type,
        }
        return render(request, 'hr/employee/form.html', context)
    else : return redirect('/access-denied')

@login
def employee_update(request, employee_id):
    chk_permission   = permission(request,"/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(EmployeeInfo, employee_id=employee_id) 
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                request.POST['salary'] = int(request.POST['salary']) if request.POST['salary'] and int(request.POST['salary']) > int(0) else 0
                request.POST['status'] = True if request.POST.get('status') == 'on' else False
                emp_photo = str(instance.photo) if instance.photo else ""
                if bool(request.FILES.get('photo', False)) == True:
                    if instance.photo and os.path.exists(str(settings.MEDIA_ROOT)+str(instance.photo)):
                        os.remove(str(settings.MEDIA_ROOT)+str(instance.photo))

                    emp_photo = request.FILES['photo']

                    if not os.path.exists(str(settings.MEDIA_ROOT)+'/employees/'):
                        os.mkdir(str(settings.MEDIA_ROOT)+'/employees/')

                    size = 200, 200
                    im = Image.open(emp_photo).convert('RGB')
                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save(str(settings.MEDIA_ROOT)+"/employees/" + str(employee_id)+".png", format="PNG", quality=80)
                    emp_photo = "/employees/" + str(employee_id)+".png"
                    
                instance.photo  = emp_photo
        
                nominee_photo = str(instance.nominee_photo) if instance.nominee_photo else ""
                if bool(request.FILES.get('nominee_photo', False)) == True:

                    if instance.nominee_photo and os.path.exists(str(settings.MEDIA_ROOT)+str(instance.nominee_photo)):
                            os.remove(str(settings.MEDIA_ROOT)+str(instance.nominee_photo))
                    nominee_photo = request.FILES['nominee_photo']

                    if not os.path.exists(str(settings.MEDIA_ROOT)+'/nominee_photo/'):
                        os.mkdir(str(settings.MEDIA_ROOT)+'/nominee_photo/')

                    size = 200, 200
                    im = Image.open(nominee_photo).convert('RGB')
                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save(str(settings.MEDIA_ROOT)+"/nominee_photo/" + str(employee_id)+".png", format="PNG", quality=80)
                    nominee_photo = "/nominee_photo/" + str(employee_id)+".png"
                    
                instance.nominee_photo = nominee_photo
                
                signature = str(instance.signature) if instance.signature else ""
                if bool(request.FILES.get('signature', False)) == True:

                    if instance.signature and os.path.exists(str(settings.MEDIA_ROOT)+str(instance.signature)):
                            os.remove(str(settings.MEDIA_ROOT)+str(instance.signature))
                    signature = request.FILES['signature']

                    if not os.path.exists(str(settings.MEDIA_ROOT)+'/employees_sign/'):
                        os.mkdir(str(settings.MEDIA_ROOT)+'/employees_sign/')

                    size = 200, 200
                    im = Image.open(signature).convert('RGB')
                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save(str(settings.MEDIA_ROOT)+"/employees_sign/" + str(employee_id)+".png", format="PNG", quality=80)
                    signature = "/employees_sign/" + str(employee_id)+".png"
                instance.signature = signature
                if request.POST.get('joining_date'): request.POST['joining_date'] = datetime.strptime(request.POST.get('joining_date'), "%d-%b-%Y").date()
                else: request.POST['joining_date'] = instance.joining_date
                form = Pf_EmployeeForm(request.POST,instance=instance)
                if form.is_valid():
                    form.save()
                    user = Users.objects.filter(employee_id = instance.employee_id)
                    if user:                     
                        company = Branch.objects.get(id = instance.emp_details_info.branch.id)
                        department , created = Departments.objects.get_or_create(name = str(instance.emp_details_info.department))
                        designation, created = Designations.objects.get_or_create(name = str(instance.emp_details_info.designation))
                        report_to = Users.objects.filter(employee_id = instance.employee_id)
                        report_to = report_to[0].id if report_to else None
                        user.update(
                            status = instance.status, branch_id = company.id,
                            department_id = department.id, 
                            designation_id = designation.id,
                            reporting_to_id = report_to, 
                            name = instance.name
                            )
                    message = request.POST.get('name')+' - Employee Successfully Updated!'
                    messages.success(request, message)
                    if not instance.status and user:
                        for s in Session.objects.all().order_by("-expire_date"):  # delete session data
                            if 'id' in s.get_decoded() and user[0].id == s.get_decoded()["id"]:
                                Session.objects.filter(session_key=s.session_key).delete()
                                break
                    employee_list = EmployeeInfo.objects.all()
                    dept_head_list = EmployeeInfo.objects.filter(status=True)
                    company_list = Brnach.objects.filter(status=True,company_id=request.session.get('company_id'))
                    department_list = Departments.objects.filter(status=True)
                    designation_list = Designations.objects.filter(status=True)
                    if request.session["role_text"] == "Admin" or request.session["role_text"] == "Super Admin":
                           employee_list = EmployeeDetails.objects.filter(branch__company_id=request.session.get('company_id'))
                    else:
                        employee_list = EmployeeDetails.objects.filter(branch_id = request.session.get('branch_id')).exclude(employee_id = 'admin')
                        
                    context = {
                        'option': "emp_list", 
                        'employee_list': "employee_list", 
                        'employee_list': employee_list,
                        'dept_head_list': dept_head_list,
                        'department_list': department_list,
                        'designation_list': designation_list,
                        'company_list': company_list,
                    }
                    return render(request, 'pf/employee_add.html', context)   
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                dept_head_list = EmployeeInfo.objects.filter(status=True)
                company_list   = Company.objects.filter(status=True)
                department_list  = Departments.objects.filter(status=True)
                designation_list = Designations.objects.filter(status=True)
                employee_type_list     = CommonMaster.objects.filter(value_for=4)
                employee_category_list = CommonMaster.objects.filter(value_for=5)
                if request.session["role_text"] == "Admin" or request.session["role_text"] == "Super Admin":
                    employee_list = EmployeeInfo.objects.all()
                else:
                    employee_list = EmployeeInfo.objects.filter(company_id = request.session.get('company_id')).exclude(employee_id = 'admin')
            
                action = {'name': 'Update', 'btnTxt': 'Update'}
                context = {
                    'dept_head_list': dept_head_list,
                    'employee': instance,
                    'employee_list': employee_list, 
                    'action': action, 
                    'department_list': department_list,
                    'designation_list': designation_list,
                    'employee_type_list':employee_type_list,
                    'employee_category_list':employee_category_list,
                    'company_list': company_list,
                }
                return render(request, 'pf/employee_add.html', context)
        else:   
            messages.warning(request,"Employee details not found!")
            return redirect('hr:employee_add')   
    else:
        return redirect('/access-denied')

@ login
def updateEmployeeStatus(request):
    chk_permission   = permission(request,"/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(EmployeeInfo, employee_id=request.GET.get('employee_id'))
        if instance.status:
            instance.status = False
            user = Users.objects.filter(employee_id = instance.employee_id)
            if user:
                user.update(status = instance.status)
                instance.save()
                for s in Session.objects.all().order_by("-expire_date"):  # delete session data
                    if 'id' in s.get_decoded() and user[0].id == s.get_decoded()["id"]:
                        Session.objects.filter(session_key=s.session_key).delete()
                        break

        else:
            instance.status = True
            Users.objects.filter(employee_id = instance.employee_id).update(status = True)
        instance.save()
        
        return HttpResponse(instance.status)   
    else:
        return HttpResponse("Access Denied") 


@login 
def import_employee2(request):
    chk_permission   = permission(request,request.path)
    if chk_permission and chk_permission.insert_action:
        if request.method == "POST":
            import_file = request.FILES['import_file']
            xl = pd.read_excel(import_file, "Sheet1") 
            new_count = 0
            for i in range(0,len(xl)):
                chk_emp = EmployeeInfo.objects.filter(employee_id = xl['Employee ID'][i])
                if not chk_emp:
                    chk_company = Company.objects.filter (short_name = xl['Company'][i])
                    chk_designation = Designations.objects.filter (name = xl['Designation'][i])
                    chk_department  = Departments.objects.filter (name = xl['Department'][i])
                    if chk_company and chk_designation and chk_department :
                        location = str(xl["Sitting Location"][i]) if str(xl["Sitting Location"][i]) != "nan" else ""
                        phone = str(xl["Phone"][i]) if str(xl["Phone"][i]) != "nan" else ""
                        pabx = str(xl["PABX"][i]) if str(xl["PABX"][i]) != "nan" else ""
                        faxNo = str(xl["Fax"][i]) if str(xl["Fax"][i]) != "nan" else ""
                        salary = str(xl["Salary"][i]) if str(xl["Salary"][i]) != "nan" else ""
                        joining_date = str(xl["Joining Date"][i]) if str(xl["Joining Date"][i]) != "nan" else ""
                        chk_report_to = EmployeeInfo.objects.filter(employee_id = xl["Report To"][i])
                        chk_report_to = int(chk_report_to[0].id) if chk_report_to else None
                        emp_add = EmployeeInfo.objects.create(
                            employee_id = xl["Employee ID"][i], name = xl["Name"][i], company_id = chk_company[0].id,
                            designation_id = chk_designation[0].id, department_id = chk_department[0].id,email = xl["Email"][i], phone_no = phone,
                            faxNo=faxNo, pabx = pabx, reporting_to_id = chk_report_to, location = location, blood_group = xl["Blood Group"][i],
                            father_name = xl["Father's Name"][i], permanent_address =xl["Permanent Address"][i],
                            contact_address = xl["Contact Address"][i], salary = salary, joining_date = joining_date, 
                            nominee_id = xl["Nominess's ID"][i], nominee_name = xl["Nominee's Name"][i], relation = xl["Relation"][i],
                            nominee_address = xl["Nominee's Address"][i], share_of_right = xl["Share of Right"][i],
                        )                                 
                        if emp_add: new_count += 1
                    else:
                        message = "Please Check the Dependence for " + xl['Employee ID'][i]
                        messages.warning(request, message)
            if new_count > 0: syncUsers(request)    #synchronus employee table with user table
            messages.success(request,str(new_count)+" employees imported.")               
            return redirect('/hr/employee-add/')  
        else : return render(request, 'hr/employee/import_employee.html')   
    else : return redirect('/access-denied')


@login 
def import_employee(request):
    chk_permission   = permission(request, request.path)
    if chk_permission and chk_permission.insert_action:
        if request.method == "POST":
            employee_ids , user   = [], get_object_or_404(Users, pk=request.session.get('id', None))
            holiday_days = {
                'Monday'    : '0',
                'Tuesday'   : '1',
                'Wednesday' : '2',
                'Thursday'  : '3',
                'Friday'    : '4',
                'Saturday'  : '5',
                'Sunday'    : '6'
            }
            import_file = request.FILES['import_file']
            xl          = pd.ExcelFile(import_file, engine='openpyxl')
            for sheet in xl.sheet_names:
                if sheet == "Personal" :
                    info = pd.read_excel(import_file, sheet, engine='openpyxl', dtype={'Employee ID':str, 'Personal Mobile':str,
                        'Father Mobile':str, 'Mother Mobile':str, 'Spouse Mobile':str, 'NID':str, 'Birth Certificate':str, 'Passport':str})
                elif sheet == "Official" :
                    info = pd.read_excel(import_file, sheet, engine='openpyxl', dtype={'Employee ID':str, 
                            'Office Mobile':str, 'Punch Card No':str, 'Gross':str})
                elif sheet == "Nominee" :
                    info = pd.read_excel(import_file, sheet, engine='openpyxl', dtype={'Employee ID':str,'Nominee Mobile':str})
                elif sheet == "Bank" :
                    info = pd.read_excel(import_file, sheet, engine='openpyxl', dtype={'Employee ID':str,'Account No':str})
                else : info = pd.read_excel(import_file, sheet, engine='openpyxl')
                for i in range(0, len(info)):
                    if sheet == "Shift":
                        chk_company = Branch.objects.filter(short_name=str_from_xls(info['Branch'][i], change_quote=False)).first()
                        try     : location, created = Location.objects.get_or_create(name=str_from_xls(info['Location'][i]))
                        except  : location = Location.objects.filter(name=str_from_xls(info['Location'][i])).first()
                        shift_id    = str_from_xls(info['Shift ID'][i])
                        name        = str_from_xls(info['Shift Name'][i])
                        day_start   = str_from_xls(info['Day Start Time'][i], time_field = True) or None
                        start_time  = str_from_xls(info['Start Time'][i], time_field = True) or None
                        grace_time  = str_from_xls(info['Grace Time'][i], time_field = True) or None
                        buffer_time = str_from_xls(info['Buffer Time'][i], time_field = True) or None
                        end_time    = str_from_xls(info['End Time'][i], time_field = True) or None
                        if shift_update := Shift.objects.filter(shift_id=shift_id).first():
                            shift_update.name           = name
                            shift_update.day_start      = day_start
                            shift_update.start_time     = start_time
                            shift_update.grace_time     = grace_time
                            shift_update.buffer_time    = buffer_time
                            shift_update.end_time       = end_time
                            shift_update.save()
                        else : Shift.objects.create(name = name, shift_id = shift_id, day_start = day_start, start_time = start_time, grace_time = grace_time, buffer_time = buffer_time, end_time = end_time, status = Status.name('Active')) 
                    else :
                        employee_id     = str_from_xls(info['Employee ID'][i])
                        employee_info   = EmployeeInfo.objects.filter(employee_id=employee_id).last()
                        employee        = EmployeeDetails.objects.filter(personal=employee_info).last()
                        if sheet == "Personal"  and employee_id :
                            first_name      = str_from_xls(info['Name'][i])
                            first_name_bn   = str_from_xls(info['Name (BN)'][i])
                            phone_no        = str_from_xls(info['Personal Mobile'][i])
                            if phone_no and not (phone_no.startswith("0") or phone_no.startswith("+88")):
                                phone_no    = "0" + phone_no
                            father_name     = str_from_xls(info['Father Name'][i])
                            father_name_bn  = str_from_xls(info['Father Name (BN)'][i])
                            father_phone_no = str_from_xls(info['Father Mobile'][i])
                            if not father_phone_no.startswith("0") or father_phone_no.startswith("+88"):
                                father_phone_no     = "0" + father_phone_no
                            mother_name     = str_from_xls(info['Mother Name'][i])
                            mother_name_bn  = str_from_xls(info['Mother Name (BN)'][i])
                            mother_phone_no = str_from_xls(info['Mother Mobile'][i])
                            if mother_phone_no and not (mother_phone_no.startswith("0") or mother_phone_no.startswith("+88")):
                                mother_phone_no = "0" + mother_phone_no
                            try     : date_of_birth = str_from_xls(info['Date of Birth (DD-MM-YYYY)'][i], date_field = True)
                            except  : date_of_birth = None
                            gender          = str_from_xls(info['Gender'][i])
                            gender          = 'Male' if gender in ['M', 'Male', 'male'] else ('Female' if gender in ['F', 'Female', 'female'] else 'Others')
                            if gender_obj  := CommonMaster.objects.filter(value_for=7, value=gender).first() : gender = gender_obj
                            else            : gender    = CommonMaster.objects.create(value_for=7, value=gender)
                            blood_group     = str_from_xls(info['Blood Group'][i])
                            religion        = str_from_xls(info['Religion'][i])
                            if religion_obj:= CommonMaster.objects.filter(value_for=3, value=religion).first() : religion = religion_obj
                            else            : religion  = CommonMaster.objects.create(value_for=3, value=religion)
                            nationality     = str_from_xls(info['Nationality'][i])
                            email           = str_from_xls(info['Personal Email'][i])
                            nid             = str_from_xls(info['NID'][i])
                            birth_certificate = str_from_xls(info['Birth Certificate'][i])
                            passport        = str_from_xls(info['Passport'][i])
                            if marital_status := str_from_xls(info['Maritial Status'][i]) :
                                if marital_status_obj  := CommonMaster.objects.filter(value_for=6, value=marital_status).first() : marital_status = marital_status_obj
                                else : marital_status   = CommonMaster.objects.create(value_for=6, value=marital_status)
                            else : marital_status       = None
                            spouse_name     = str_from_xls(info['Spouse Name'][i])
                            spouse_name_bn  = str_from_xls(info['Spouse Name (BN)'][i])
                            spouse_phone_no = str_from_xls(info['Spouse Mobile'][i])
                            if spouse_phone_no and not (spouse_phone_no.startswith("0") or spouse_phone_no.startswith("+88")):
                                spouse_phone_no     = "0" + spouse_phone_no
                            no_of_children  = str_from_xls(info['Number Of Children'][i]) or 0
                            permanent_postcode      = str_from_xls(info['Permanent Post Code'][i])
                            permanent_location      = GEOLocation.objects.filter(postcode_en=permanent_postcode).first()
                            permanent_address       = str_from_xls(info['Permanent Address'][i])
                            permanent_address_bn    = str_from_xls(info['Permanent Address (BN)'][i])
                            present_postcode        = str_from_xls(info['Present  Post Code'][i])
                            present_location        = GEOLocation.objects.filter(postcode_en=present_postcode).first()
                            present_address         = str_from_xls(info['Present Address'][i])
                            present_address_bn      = str_from_xls(info['Present Address (BN)'][i])
                            
                            if not employee_info :
                                if emp_add := EmployeeInfo.objects.create(employee_id=employee_id, status=True,
                                    first_name=first_name, first_name_bn=first_name_bn, phone_no=phone_no,
                                    father_name=father_name, father_name_bn=father_name_bn, father_phone_no=father_phone_no,
                                    mother_name=mother_name, mother_name_bn=mother_name_bn, mother_phone_no=mother_phone_no,
                                    date_of_birth=date_of_birth, gender=gender, blood_group=blood_group, religion=religion,
                                    nationality=nationality, email=email, nid=nid, birth_certificate=birth_certificate, passport=passport,
                                    marital_status=marital_status, spouse_name=spouse_name, spouse_name_bn=spouse_name_bn,
                                    spouse_phone_no=spouse_phone_no, no_of_children=int(float(no_of_children)),
                                    permanent_location=permanent_location, permanent_address=permanent_address,
                                    permanent_address_bn=permanent_address_bn, present_location=present_location,
                                    present_address=present_address, present_address_bn=present_address_bn,
                                    employee_status=Status.name('active'), created_by=user) : employee_ids.append(employee_id)
                            elif employee_info :
                                if emp_update := EmployeeInfo.objects.filter(employee_id=employee_id).update(status=True,
                                    first_name=first_name, first_name_bn=first_name_bn, phone_no=phone_no,
                                    father_name=father_name, father_name_bn=father_name_bn, father_phone_no=father_phone_no,
                                    mother_name=mother_name, mother_name_bn=mother_name_bn, mother_phone_no=mother_phone_no,
                                    date_of_birth=date_of_birth, gender=gender, blood_group=blood_group, religion=religion,
                                    nationality=nationality, email=email, nid=nid, birth_certificate=birth_certificate, passport=passport,
                                    marital_status=marital_status, spouse_name=spouse_name, spouse_name_bn=spouse_name_bn,
                                    spouse_phone_no=spouse_phone_no, no_of_children=int(float(no_of_children)),
                                    permanent_location=permanent_location, permanent_address=permanent_address,
                                    permanent_address_bn=permanent_address_bn, present_location=present_location,
                                    present_address=present_address, present_address_bn=present_address_bn,
                                    employee_status=Status.name('active'), updated_by=user) : employee_ids.append(employee_id)
                        elif employee_id and employee_info and sheet == "Official" :
                            if company := Branch.objects.filter(name__iexact=str_from_xls(info['Branch'][i], change_quote=False)).first() :
                                division, sub_section, department, designation, section, unit, location, building, floor, line, pabx = None, None, None, None, None, None, None, None, None, None, None
                                employee_category, employee_type, skill_category, initial_grade, grade, punch_id, tin = None, None, None, None, None, None, None
                                # if division_text     := str_from_xls(info['Division'][i]) :
                                #     if division_obj  := Division.objects.filter(name=division_text).first()  : 
                                #         division = division_obj
                                #         division.status = Status.name('Active')
                                #         division.save()
                                #     else : division   = Division.objects.create(name=division_text, status=Status.name('Active'))
                                # if sub_section_text     := str_from_xls(info['Subsection'][i]) :
                                #     if sub_section_obj  := SubSection.objects.filter(division=division, name=sub_section_text).first()  : 
                                #         sub_section = sub_section_obj
                                #         sub_section.status = Status.name('Active')
                                #         sub_section.save()
                                #     else : sub_section   = SubSection.objects.create(division=division, name=sub_section_text, status=Status.name('Active'))
                                if department_text     := str_from_xls(info['Department'][i]) :
                                    if department_obj  := Departments.objects.filter(name=department_text).first()  : department = department_obj
                                    else : department   = Departments.objects.create(name=department_text)
                                if designation_text    := str_from_xls(info['Designation'][i]) :
                                    if designation_obj := Designations.objects.filter(name=designation_text).first(): designation = designation_obj
                                    else : designation  = Designations.objects.create(name=designation_text)
                                if section_text        := str_from_xls(info['Section'][i]) :
                                    if section_obj     := Sections.objects.filter(department=department, name=section_text).first() : 
                                        section = section_obj
                                        section.status = Status.name('Active')
                                        section.save()
                                    else : section      = Sections.objects.create(department=department, name=section_text, status=Status.name('Active'), created_by=user)
                                # cost_center             = Company.objects.filter(short_name__iexact=str_from_xls(info['Cost Center'][i], change_quote=False)).first()
                                # if unit_text           := str_from_xls(info['Unit'][i]) :
                                #     if unit_obj        := CommonMaster.objects.filter(value_for=44, value=unit_text).first() : unit = unit_obj
                                #     else : unit         = CommonMaster.objects.create(value_for=44, value=unit_text)
                                if location_text       := str_from_xls(info['Sitting Location'][i]) :
                                    if location_obj    := Location.objects.filter(name=location_text).first() : 
                                        location = location_obj
                                        location.status = Status.name('Active')
                                        location.save()
                                    else : location     = Location.objects.create(name=location_text, status=Status.name('Active'), created_by=user)
                                # if building_text       := str_from_xls(info['Building'][i]) :
                                #     if building_obj    := Building.objects.filter(location=location, name=building_text).first() : 
                                #         building = building_obj
                                #         building.status = Status.name('Active')
                                #         building.save()
                                #     else : building     = Building.objects.create(location=location, name=building_text, status=Status.name('Active'), created_by=user)
                                
                                if employee_category_text  := str_from_xls(info['Employee Category'][i]) :
                                    if employee_category_obj:= CommonMaster.objects.filter(value_for=5, value=employee_category_text).first() : employee_category = employee_category_obj
                                    else : employee_category = CommonMaster.objects.create(value_for=5, value=employee_category_text)
                                if employee_type_text      := str_from_xls(info['Employment  Type'][i]) :
                                    if employee_type_obj   := CommonMaster.objects.filter(value_for=4, value=employee_type_text).first() : employee_type = employee_type_obj
                                    else : employee_type    = CommonMaster.objects.create(value_for=4, value=employee_type_text)
                                reporting_to                = EmployeeDetails.objects.filter(personal__employee_id=str_from_xls(info['Reporting Boss Employee ID'][i])).last()
                                if not reporting_to         :
                                    reporting_to_dept_head  = Users.objects.filter(department=department, branch=company, is_department_head=True, status=True).first()
                                    if reporting_to_dept_head : reporting_to = EmployeeDetails.objects.filter(personal__employee_id=reporting_to_dept_head.employee_id).first()
                                if skill_category_text     := str_from_xls(info['Skill Category'][i]) :
                                    if skill_category_obj  := CommonMaster.objects.filter(value_for=8, value=skill_category_text).first() : skill_category = skill_category_obj
                                    else : skill_category   = CommonMaster.objects.create(value_for=8, value=skill_category_text)
                                initial_grade       = str_from_xls(info['Initial Grade'][i])
                                grade               = str_from_xls(info['Current Grade'][i])
                                punch_id            = str_from_xls(info['Punch Card No'][i])
                                try : pabx          = str_from_xls(info['PABX'][i]) or ""
                                except : pabx       = None
                                office_mobile       = str_from_xls(info['Office Mobile'][i])
                                if office_mobile and not (office_mobile.startswith("0") or office_mobile.startswith("+88")): office_mobile = "0" + office_mobile
                                office_email        = str_from_xls(info['Office Email'][i])
                                tin                 = str_from_xls(info['TIN'][i])
                                try : joining_date  = str_from_xls(info['Date of Joining (DD-MM-YYYY)'][i], date_field = True)
                                except:joining_date = None
                                provision_month     = str_from_xls(info['Provision(Month)'][i])
                                if not (isinstance(i, int)) : provision_month = ''
                                shift               = Shift.objects.filter(shift_id=str_from_xls(info['Shift'][i])).first()
                                try     : salary    = str_from_xls(info['Gross'][i]) or 0
                                except  : salary    = 0
                                holidays            = str_from_xls(info['Weekly Off Day'][i])
                                holidays            = holidays.split(",") if holidays else []
                                holiday             = [holiday_days[d.strip()] for d in holidays]
                                income_tax          = True if str_from_xls(info['Income Tax'][i]).title()   == "Yes" else False
                                tiffin_bill         = True if str_from_xls(info['Tiffin Bill'][i]).title()  == "Yes" else False
                                transport_facility  = True if str_from_xls(info['Transport'][i]).title()    == "Yes" else False
                                has_pf              = True if str_from_xls(info['PF Facility'][i]).title()  == "Yes" else False
                                overtime            = True if str_from_xls(info['Over Time'][i]).title()    == "Yes" else False
                                off_day_ot          = True if str_from_xls(info['Off Day OT'][i]).title()   == "Yes" else False
                                holiday_bonus       = True if str_from_xls(info['Holiday Bonus'][i]).title()== "Yes" else False
                                if not employee :
                                    if emp_details := EmployeeDetails.objects.create(personal=employee_info, employee_id=employee_id, branch=company, department=department, designation=designation, section=section,location=location,employee_type=employee_type, employee_category=employee_category, reporting_to=reporting_to, pabx=pabx, skill_category=skill_category, initial_grade=initial_grade, grade=grade, punch_id=punch_id, office_mobile=office_mobile, office_email=office_email, tin=tin, joining_date=joining_date, provision_month=provision_month, shift=shift, salary=salary, holiday=holiday, income_tax=income_tax, tiffin_bill=tiffin_bill, transport_facility=transport_facility, has_pf=has_pf, overtime=overtime, off_day_ot=off_day_ot, holiday_bonus=holiday_bonus, created_by=user, status=Status.name('active')) : employee_ids.append(employee_id)
                                elif employee :
                                    if emp_details_update := EmployeeDetails.objects.filter(personal=employee_info, employee_id=employee_id).update(branch=company,department=department, designation=designation, section=section, location=location,employee_category=employee_category, employee_type=employee_type, reporting_to=reporting_to, skill_category=skill_category, grade=grade, initial_grade=initial_grade, punch_id=punch_id, pabx=pabx, tin=tin, office_mobile=office_mobile, office_email=office_email, holiday=holiday, joining_date=joining_date, provision_month=provision_month, shift=shift, salary=salary, income_tax=income_tax, tiffin_bill=tiffin_bill, transport_facility=transport_facility, has_pf=has_pf, overtime=overtime, off_day_ot=off_day_ot, holiday_bonus=holiday_bonus, created_by=user, status=Status.name('active')) : employee_ids.append(employee_id)
                                emp_details = EmployeeDetails.objects.filter(personal=employee_info).first()
                                if emp_details: create_user(emp_details)
                        elif employee_id and employee :
                            if sheet == "Nominee" :
                                nominee_name    = str_from_xls(info['Nominee Name'][i])
                                nominee_nid     = str_from_xls(info['Nominee NID'][i])
                                relation        = str_from_xls(info['Relation'][i])
                                nominee_mobile  = str_from_xls(info['Nominee Mobile'][i])
                                if nominee_mobile and not (nominee_mobile.startswith("0") or nominee_mobile.startswith("+88")): nominee_mobile  = "0" + nominee_mobile
                                nominee_address = str_from_xls(info['Address'][i])
                                share_of_right  = str_from_xls(info['Share Of Right'][i])
                                if nominee_info := EmployeeNominee.objects.filter(employee=employee, nominee_nid=nominee_nid).last() :
                                    if emp_nominee_update := EmployeeNominee.objects.filter(employee=employee, nominee_nid=nominee_nid).update(nominee_name=nominee_name, nominee_mobile=nominee_mobile, share_of_right=share_of_right, nominee_address=nominee_address, relation=relation, updated_by=user) : employee_ids.append(employee_id)
                                else :
                                    if emp_nominee := EmployeeNominee.objects.create(employee=employee, nominee_name=nominee_name, nominee_nid=nominee_nid, relation=relation, nominee_mobile=nominee_mobile, nominee_address=nominee_address, share_of_right=share_of_right, status=Status.name('active'), created_by=user) : employee_ids.append(employee_id)
                            elif sheet == "Bank" :
                                bank_name   = str_from_xls(info['Bank Name'][i])
                                branch_name = str_from_xls(info['Branch Name'][i])
                                account_no  = str_from_xls(info['Account No'][i])
                                status      = str_from_xls(info['Status'][i])
                                if bank_info := EmployeeBankInfo.objects.filter(employee=employee, bank_name=bank_name, account_no=account_no).last(): 
                                    if emp_bank_update := EmployeeBankInfo.objects.filter(employee=employee, bank_name=bank_name, account_no=account_no).update(branch_name=branch_name, status=Status.name(status), updated_by=user) : employee_ids.append(employee_id)
                                else :
                                    if emp_bank := EmployeeBankInfo.objects.create(employee=employee, bank_name=bank_name, branch_name=branch_name, account_no=account_no, status=Status.name(status), created_by=user) : employee_ids.append(employee_id)
            messages.success(request, "You have successfully imported {} employee/s information.".format(len(set(employee_ids))))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else : return render(request, 'hr/employee/import_employee.html')   
    else : return redirect('/access-denied')

def create_user(emp_details=None):
    if user_role_obj   := UserRoles.objects.filter(name='User').first() : user_role = user_role_obj
    else : user_role    = UserRoles.objects.create(name='User')
    if not Users.objects.filter(employee_id=emp_details.personal.employee_id) and emp_details:
        report_to, md5_obj = None, hashlib.md5(emp_details.personal.employee_id.encode())
        encripted_pass = md5_obj.hexdigest()
        if emp_details.reporting_to: report_to = Users.objects.filter(employee_id=emp_details.reporting_to.employee_id).last()
        Users.objects.create(branch_id=emp_details.branch_id, department_id=emp_details.department_id, designation_id=emp_details.designation_id, 
            password=encripted_pass, password_text=emp_details.personal.employee_id, employee_id=emp_details.personal.employee_id.strip(), 
            name=emp_details.name, role_id=user_role.id, email=emp_details.office_email, reporting_to=report_to) 

@login
def outside_remote_duty(request):
    chk_permission   = permission(request,"/hr/outside-remote-duty/")
    if chk_permission and chk_permission.insert_action:
        try:
            if request.method=='POST':
                request.POST = request.POST.copy()
                if not OutsideRemoteDuty.objects.filter(date = request.POST["date"], employee_id = request.POST["employee_id"]).exclude(status= Status.name('Rejected')):
                    request.POST["created_by"] = int(request.session.get('id'))
                    form = OutsideRemoteDutyForm(request.POST)
                    if form.is_valid():
                        application = form.save()
                        application.reporting_boss = application.created_by.reporting_to
                        application.reporting_boss_checked_at
                        if request.session.get('is_head') == True:
                            application.status = Status.name('Approved')
                            application.reporting_boss_checked_at = application.created_at
                            employee = EmployeeDetails.objects.filter(personal__employee_id=application.employee_id).first()
                            Attendance.objects.create(employee=employee, present_day=application.date, in_time=application.in_time, out_time=application.out_time, outside_office=True).save()
                        else : 
                            application.status = Status.name('Pending')
                            # send notification
                            n_sender        = application.created_by
                            n_action_url    = reverse('hr:outside_remote_duty')
                            n_model         = 'OutsideRemoteDuty'
                            n_verb          = 'Outside Duty Raised'
                            n_description   = "1 new Outside Duty Raised in HR"
                            notify.send(n_sender, recipient=application.reporting_boss, action_url=n_action_url,
                                model=n_model, verb=n_verb, description=n_description, is_repeated=True)
                        application.save()
                        messages.success(request,'Outside/Remote Duty Added Successfully')
                    else : ebs_bl_common.form_errors(request, form)
                else : messages.warning(request, "Duty in same date is already exists!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            context = {
                "self_duty_list": OutsideRemoteDuty.objects.filter(created_by=request.session.get("id")).order_by('-date'),
                "approval_pending_list": OutsideRemoteDuty.objects.filter(reporting_boss_id=request.session.get("id"), status_id= 34).order_by('-date'),
                "approved_list": OutsideRemoteDuty.objects.filter(reporting_boss_id=request.session.get("id"), status_id= 7).order_by('-date'),
            }
            return render(request, 'hr/attendance/outside_remote_duty.html', context)
        except Exception as e:
            messages.warning(request,str(e))   
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else : return redirect('/access-denied')
    
@login
def outside_duty_approve(request, id):
    chk_permission   = permission(request,"/hr/outside-remote-duty/")
    if chk_permission and chk_permission.view_action:
        OutsideRemoteDuty(id=id, status=Status.name('Approved'), reporting_boss_checked_at=datetime.now()).save(update_fields=["status_id", "reporting_boss_checked_at"]) 
        
        # Attendance data sync
        instance = OutsideRemoteDuty.objects.get(id=id)
        employee = EmployeeDetails.objects.get(personal_id=(EmployeeInfo.objects.get(employee_id=instance.employee_id)).id)
        Attendance(employee_id=employee.id, present_day=instance.date, in_time=instance.in_time, out_time=instance.out_time, outside_office=True).save() 
        messages.success(request, 'Data sync with attendance!')
        # Attendance data sync
        
        # send notification
        n_sender        = instance.reporting_boss
        n_action_url    = reverse('hr:outside_remote_duty')
        n_model         = 'OutsideRemoteDuty'
        n_verb          = 'Outside Duty Approved'
        n_description   = "1 new Outside Duty Approved in HR"
        notify.send(n_sender, recipient=instance.created_by, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
        # send notification
        
        messages.success(request, 'Duty Approved!')
        context = { "option": "approval_pending_list" }
        return redirect("/hr/outside-remote-duty/", context) 
    else : return JsonResponse('You have no access on this action!',safe=False)
    
@login
def outside_duty_reject(request, id):
    chk_permission   = permission(request,"/hr/outside-remote-duty/")
    if chk_permission and chk_permission.view_action:
        OutsideRemoteDuty(id=id, status=Status.name('Rejected'), reporting_boss_checked_at=datetime.now()).save(update_fields=["status_id", "reporting_boss_checked_at"]) 
        messages.success(request, 'Duty Rejected!')
        
        # send notification
        instance        = OutsideRemoteDuty.objects.get(id=id)
        n_sender        = instance.reporting_boss
        n_action_url    = reverse('hr:outside_remote_duty')
        n_model         = 'OutsideRemoteDuty'
        n_verb          = 'Outside Duty Rejected'
        n_description   = "1 new Outside Duty Rejected in HR"
        notify.send(n_sender, recipient=instance.created_by, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
        # send notification
        
        return redirect("/hr/outside-remote-duty/") 
    else : return JsonResponse('You have no access on this action!',safe=False)
    
@login
def outside_duty_delete(request, id):
    chk_permission   = permission(request,"/hr/outside-remote-duty/")
    if chk_permission and chk_permission.view_action and chk_permission.delete_action:
        OutsideRemoteDuty.objects.filter(id = id).delete()
        return JsonResponse('Duty Delete Successful.',safe=False)
    else : return JsonResponse('You have no access on this action!',safe=False)

# Payroll Functions Start
@login
def slab_list(request):
    chk_permission   = permission(request,"/hr/salary-slab/")
    if chk_permission and chk_permission.view_action:
        context = { "slab_list": HRSalarySlabMaster.objects.all() }
        return render(request, 'hr/salary/slab_list.html', context)
    else : return redirect('/access-denied')

@login
def income_tax_slab(request):
    chk_permission   = permission(request,"/hr/income-tax-slab/")
    if chk_permission and chk_permission.view_action:
        context = { "slab_list": HRIncomeTaxSlabMaster.objects.all() }
        return render(request, 'hr/salary/income_tax_slab.html', context)
    else : return redirect('/access-denied')

@login
def income_tax_slab(request):
    chk_permission   = permission(request,"/hr/income-tax-slab/")
    if chk_permission and chk_permission.insert_action:
        try:
            if request.method=='POST':
                request.POST = request.POST.copy()
                if not HRIncomeTaxSlabMaster.objects.filter(from_amount = request.POST["from_amount"]):
                    request.POST["created_by"] = int(request.session.get('id'))
                    form = HRIncomeTaxSlabForm(request.POST)
                    if form.is_valid():
                        form.save()
                        messages.success(request,'Income Tax Slab Setup Successful')
                    else:
                        for field in form:
                            for error in field.errors:
                                messages.warning(request, "%s : %s" % (field.name, error)) 
                else:
                    messages.warning(request, "This tax slab already exists!")                    
            context = {
                "action_name": "save",
                "slab_list": HRIncomeTaxSlabMaster.objects.all()
            }
            return render(request, 'hr/salary/income_tax_slab.html', context)
        except Exception as e:
            messages.warning(request,str(e))   
            return redirect("/hr/income-tax-slab/") 
    else : return redirect('/access-denied')

@login
def income_tax_slab_update(request, id):
    chk_permission   = permission(request,"/hr/income-tax-slab/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        try:
            instance = get_object_or_404(HRIncomeTaxSlabMaster, id=id)
            form     = HRIncomeTaxSlabForm(instance=instance)
            if request.method == 'POST':
                request.POST = request.POST.copy()
                request.POST["updated_by"] = int(request.session.get('id'))
                form = HRIncomeTaxSlabForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    message = 'Income Tax Slab Successfully Updated!'
                    messages.success(request, message)
                else:
                    messages.warning(request, str(request.POST["slab_name"])+" slab name already exists!")                
                context = {
                    "option": "list",
                    "slab_list": HRIncomeTaxSlabMaster.objects.all()
                }
                return redirect('/hr/income-tax-slab/', context)           
            else:
                context = {
                    "slab": instance,
                    "action_name": "Update",
                    "slab_list": HRIncomeTaxSlabMaster.objects.all()
                }
                return render(request, 'hr/salary/income_tax_slab.html', context)
        except Exception as e:
            messages.warning(request,str(e))   
            return redirect("/hr/income-tax-slab/") 
    else : return redirect('/access-denied')

@login
def income_tax_slab_delete(request, id):
    chk_permission   = permission(request,"/hr/income-tax-slab/")
    if chk_permission and chk_permission.view_action and chk_permission.delete_action:
        HRIncomeTaxSlabMaster.objects.filter(id = id).delete()
        return JsonResponse('Income Tax Slab Delete Successful.',safe=False)
    else: return JsonResponse('You have no access on this action!',safe=False)

@login
def salary_breakdown(request):
    chk_permission   = permission(request,"/hr/salary-breakdown/")
    if chk_permission and chk_permission.view_action:
        context = {
            "salary_breakdown_list": HRSalaryBreakdown.objects.all(),
        }
        return render(request, 'hr/salary/salary_breakdown.html', context)
    else:
        return redirect('/access-denied')
    
@login 
def import_other_salary_amounts(request):
    # chk_permission   = permission(request,request.path)
    # if chk_permission and chk_permission.insert_action:
    if request.session.get('employee_id', '') in ['NGO00001001'] :
        if request.method == "POST":
            import_file = request.FILES['import_file']
            xl = pd.read_excel(import_file, "Sheet1") 
            new_count = 0
            year = request.POST.get('year')
            month = request.POST.get('month')
            for i in range(0,len(xl)):
                employee = EmployeeDetails.objects.get(personal__employee_id = xl['Employee ID'][i])
                heads = HRSalarySlabMaster.objects.get(heads= xl['Heads'][i])
                amount = str(abs(xl["Amount"][i])) if str(abs(xl["Amount"][i])) != "nan" else ""
                
                other_salary_amount_add = HRMontlySalaryDetails.objects.create(
                    year = year,
                    month = month,
                    heads = heads,
                    employee = employee,
                    amount = amount,
                )                                 
                if other_salary_amount_add: new_count += 1
                    
            if new_count==0 : messages.warning(request, "May be data exist or there are some problem")  
            else : messages.success(request,str(new_count)+" Data Imported successfully. Thank you")               
            return redirect('/hr/salary-process/')  
        else : 
            context = {
                'months'        : [[m[0], m[1]] for m in HRMontlySalaryDetails.month_list],
                'years'         : ['2023', '2024', '2025', '2026', '2027'],
            }
            return render(request, 'hr/salary/import_other_salary_amounts.html', context)   
    else : return redirect('/access-denied')
    
@login 
def import_gross_salary_amounts(request):
    # chk_permission   = permission(request,request.path)
    # if chk_permission and chk_permission.insert_action:
        
    if request.session.get('employee_id', '') in ['NGO00001001'] :
        if request.method == "POST":
            import_file = request.FILES['import_file']
            xl, new_count = pd.read_excel(import_file, "Sheet1"), 0
            for i in range(0,len(xl)):
                employee = EmployeeDetails.objects.get(personal__employee_id = xl['Employee ID'][i])
                employee.salary = str(abs(xl["Amount"][i])) if str(abs(xl["Amount"][i])) != "nan" else 0
                employee.save()
                new_count += 1
            if new_count==0 : messages.warning(request, "There are some problem!")  
            else : messages.success(request,str(new_count)+" Data Imported successfully. Thank you")               
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else : return render(request, 'hr/salary/import_gross_salary_amounts.html', {})   
    else : return redirect('/access-denied')

# @login
# def salary_process_execution(request):
#     chk_permission   = permission(request,"/hr/salary-process-execution/")
#     if chk_permission and chk_permission.view_action:
#         context = {
            
#         }
#         return render(request, 'hr/salary/salary_process.html', context)
#     else:
#         return redirect('/access-denied')

# Payroll Functions End

@login
def pf_master_add(request):
    chk_permission   = permission(request,"/hr/pf_master_add/")
    if chk_permission and chk_permission.insert_action:
        if request.method == 'POST':
            request.POST = request.POST.copy()
            form = ProvidentFundMasterForm(request.POST)
            if form.is_valid():
                obj = form.save()
                obj.save()
                message =  message = ' Pf Successfully Saved!'
                messages.success(request, message)

                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                        pfmaster_list = ProvidentFundMaster.objects.all()
                else:
                    pfmaster_list = ProvidentFundMaster.objects.filter(company_id = request.session.get('company_id'))
                action = {'name': 'Add New', 'btnTxt': 'Submit'}

                context = {
                    'option': "pf_master_list",
                    'action': action, 
                    'pf_master_list': pfmaster_list,
                }

            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error))
            return redirect('hr:pf_master_add')
        else:
            company_list = Company.objects.filter(status=True)

            if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                   pfmaster_list = ProvidentFundMaster.objects.all()
            else:
                pfmaster_list = ProvidentFundMaster.objects.filter(company_id = request.session.get('company_id'))

            action = {'name': 'Add New', 'btnTxt': 'Submit'}
            context = {
                'action': action, 
                'company_list': company_list,
                'pf_master_list': pfmaster_list,
            }
        return render(request, 'pf/pf_master_add.html', context)
    else:
        return redirect('/access-denied')

@login
def pf_master_update(request, id):
    chk_permission   = permission(request,"/hr/pf_master_add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(ProvidentFundMaster, id=id)
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                form = ProvidentFundMasterForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    message = ' Pf Successfully Updated'
                    messages.success(request, message)
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                company_list = Company.objects.filter(status=True)

                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                        pfmaster_list = ProvidentFundMaster.objects.all()
                else:
                    pfmaster_list = ProvidentFundMaster.objects.filter(company_id = request.session.get('company_id'))
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    'option': "pf_master_list",
                    'action': action, 
                    'company_list': company_list,
                    'pf_master_list': pfmaster_list,
                }           
                return render(request, 'pf/pf_master_add.html', context)
            else:
                company_list = Company.objects.filter(status=True)
                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                    pfmaster_list = ProvidentFundMaster.objects.all()
                else:
                    pfmaster_list = ProvidentFundMaster.objects.filter(company_id = request.session.get('company_id'))
                action = {'name': 'Update', 'btnTxt': 'Update'}
                context = {
                    'pf_master': instance, 
                    'action': action, 
                    'company_list': company_list,
                    'pf_master_list': pfmaster_list,
                }
                return render(request, 'pf/pf_master_add.html', context)
        else:   
            messages.warning(request,"Pf details not found!")
            return redirect('hr:pf_master_list')        
    else:
        return redirect('/access-denied')

@login
def delete_pf_master(request, id):
    chk_permission   = permission(request,"/hr/pf_master_add/")
    if chk_permission.delete_action:
        ProvidentFundMaster.objects.filter(id=id).delete()
        message = ' Pf Deleted!'
        messages.success(request, message)
        return JsonResponse('Provident Fund Delete Successful.', safe=False)
    else:
        return JsonResponse('You have no access on this action!', safe=False)

@login
def pf_policy_master_add(request):
    chk_permission   = permission(request, "/hr/pf-policy-master-add/")
    if chk_permission and chk_permission.insert_action:
        if request.method == 'POST':
            request.POST = request.POST.copy()
            form = PolicyMasterForm(request.POST)
            if form.is_valid():
                obj = form.save()
                obj.save()
                message = 'Pf Policy Successfully Created!'
                messages.success(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error)) 
            return redirect('hr:pf_policy_master_add')
        else:
            if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                   pf_policy_master_list = PolicyMaster.objects.all()
            else:
                pf_policy_master_list = PolicyMaster.objects.filter(company_id = request.session.get('company_id'))
            action = {'name': 'Add New', 'btnTxt': 'Submit'}
            context = {
                'pf_policy_master_list' : pf_policy_master_list,
                'action': action, 
            }
        return render(request, 'pf/pf_policy_master_add.html', context)
    else:
        return redirect('/access-denied')

@login
def pf_policy_master_update(request, id):
    chk_permission   = permission(request, '/hr/pf-policy-master-add/')
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(PolicyMaster, id=id)
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                form = PolicyMasterForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    message = ' Pf Policy Successfully Updated!'
                    messages.success(request, message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                return redirect('hr:pf_policy_master_add')
            else:
                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                      pf_policy_master_list = PolicyMaster.objects.all()
                else:
                      pf_policy_master_list = PolicyMaster.objects.filter(company_id = request.session.get('company_id'))
                action = {'name': 'Update', 'btnTxt': 'Update'}
                context = {
                    'pf_policy_master': instance, 
                    'action': action, 
                    'pf_policy_master_list' : pf_policy_master_list
                }
                return render(request, 'pf/pf_policy_master_add.html', context)
        else:   
            messages.warning(request,"Policy details not found!")
            return redirect('hr:pf_policy_master_add')         
    else:
        return redirect('/access-denied')


@login
def delete_pf_policy_master(request, id):
    chk_permission   = permission(request, '/hr/pf-policy-master-add/')
    if chk_permission.delete_action:
        PolicyMaster.objects.filter(id=id).delete()
        message = ' Pf Policy Deleted!'
        messages.success(request, message)
        return JsonResponse('Provident Fund Delete Successful.', safe=False)
    else:
        return JsonResponse('You have no access on this action!', safe=False)

@login
def pf_eligible_list(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
            pf_emp_list = EmployeePF.objects.values_list('employee_id',flat=True)
            employee_eligible = EmployeeDetails.objects.filter(status = True, joining_date__isnull = False).exclude(Q(id__in = pf_emp_list)|Q(has_pf = True))
            emply_data_list=[]
            request.session['employee_pf'] = " "
            for data in employee_eligible: 
                joining_date = data.joining_date
                to_date = datetime.now().date()
                date1 = datetime(joining_date.year, joining_date.month, joining_date.day)
                date2 = datetime(to_date.year, to_date.month, to_date.day)
                diff = relativedelta.relativedelta(date1, date2)
                year = abs(int(diff.years)) 
                month = abs(int(diff.months))
                day = abs(int(diff.days))
                tenure = str(year)+ " years "+str(month) + " month "+str(day)+" days"
                if year >= 1:
                    pf_obj={
                        'id' : data.id,
                        'employee_id':data.personal.employee_id,
                        'name': data.personal.name,
                        'joining_date' : data.joining_date,
                        'company' : data.company,
                        'department' : data.department,
                        'designation' : data.designation,
                        'status' : data.status,
                        'salary' : data.salary,
                        'has_pf' : data.has_pf,
                        'tenure' : tenure
                    }
                    emply_data_list.append(pf_obj)
            context = {
                'emply_data_list' : emply_data_list,  
                }
            return render (request, 'pf/Pf_eligible_list.html', context)
    else:
        return redirect('/access-denied')

@login
def pf_employee_enrollment_list(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
            employee_pf_list = EmployeePF.objects.all()
        else:
            employee_pf_list = EmployeePF.objects.filter(company_id = request.session.get('company_id'))
        Pf_list = ProvidentFundMaster.objects.all()
        context = {
            'employee_pf_list':employee_pf_list,
            'Pf_list' : Pf_list
        }
        return render(request, 'pf/pf_enrollment_list.html', context)
    else:
        return redirect('/access-denied')

@csrf_exempt
def get_employee_enrollment_list_filter(request):
    data_list = []
    search_text = request.POST.get('search_text','').strip()
    start       = int(request.POST.get('start', 0))
    pf          = request.POST.get('pf','')
    start_date  = request.POST.get('start_date', '')
    end_date    = request.POST.get('end_date', '') 
    if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
        employee_pf_list = EmployeePF.objects.all()
    else:
        employee_pf_list = EmployeePF.objects.filter(company_id = request.session.get('company_id'))


    if search_text: employee_pf_list = employee_pf_list.filter(Q(employee__employee_id__icontains=search_text)|Q(employee__name__icontains=search_text))

    if start_date or end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date + timedelta(days=1)
        employee_pf_list = employee_pf_list.filter(date_Pf_membership__gte=start_date, date_Pf_membership__lt=end_date)

    if pf:  employee_pf_list= employee_pf_list.filter(pf = pf)

    employee_pf_list = employee_pf_list[start:start + 20]
    for enroll in employee_pf_list:
        employee = enroll.employee.employee_id if enroll.employee.employee_id else 'N/A'
        name     = enroll.employee.name if enroll.employee.name else 'N/A' 
        pf       = enroll.pf.pf_heading if enroll.pf.pf_heading else 'N/A'
        basis_of_contribution = enroll.basis_of_contribution if enroll.basis_of_contribution else 'N/A'
        basic_gross_salary    = enroll.basic_gross_salary if enroll.basic_gross_salary else 'N/A'
        date_Pf_membership    = enroll.date_Pf_membership if enroll.date_Pf_membership else 'N/A'
        rate_employee_contribution    = enroll.rate_employee_contribution if enroll.rate_employee_contribution else 'N/A'
        rate_company_contribution    = enroll.rate_company_contribution if enroll.rate_company_contribution else 'N/A'
        emp_opening_contribution    = enroll.emp_opening_contribution if enroll.emp_opening_contribution else 'N/A'
        company_opening_contribution = enroll.company_opening_contribution if enroll.company_opening_contribution else 'N/A' 
        
        action =""  

        edit_url = reverse('hr:employee_pf_update', kwargs={'id': enroll.id})
        edit = '<a class="h4 m-r-10 text-success" href="' + edit_url + '" class="h4 text-danger" title="Update">'
        edit += '<span class="icon"><i class="ti-pencil-alt"></i></span></a>'
        action += edit
        data = [employee, name, pf, basis_of_contribution, basic_gross_salary, date_Pf_membership,rate_employee_contribution,rate_company_contribution, emp_opening_contribution, company_opening_contribution,action]
        data_list.append(data)

    return JsonResponse(data_list, safe=False)


@login
def employee_pf_add(request,id):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        request.session['employee_pf'] = "save_pf"
        instance = get_object_or_404(EmployeeInfo, id=id)
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                if request.POST.get('status') == "on": request.POST["status"] = Status.name('active')
                else: request.POST["status"]  =Status.name('inactive')
                request.POST["rate_company_contribution"]    = request.POST.get('rate_company_contribution')
                request.POST["employee"]    = id
                request.POST["has_pf"]      = True
                request.POST["salary"]      = "basic_gross_salary"
                request.POST['date_Pf_membership'] = datetime.strptime(request.POST.get('date_Pf_membership'), "%d-%b-%Y").date() if request.POST.get('date_Pf_membership') else ''
                form = EmpPfRegistationForm(request.POST)
                if form.is_valid():
                    form.save()
                    EmployeeDetails.objects.filter(id = instance.employee_details.last().id, has_pf = False).update(has_pf=True)
                    request.session['employee_pf'] = None
                    message = 'Employee Pf Successfully Created!' 
                    messages.success(request, message)
                    return redirect("hr:pf_emp_enroll_list")                  
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                pf_list     = ProvidentFundMaster.objects.all()
                policy_list = PolicyMaster.objects.all()
                employee_salary = EmployeeInfo.objects.filter(status = True)
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    'action'            : action,
                    'policy_list'       : policy_list,
                    'employee_salary'   : employee_salary,
                    'instance'          : instance,
                    'pf_list'           : pf_list
                }
            return render (request, 'pf/pf_emp_create.html', context)
        else:   
            messages.warning(request,"PF details not found!")
            return redirect('hr:employee_pf_add')
    else:
        return redirect('/access-denied')

@login
def employee_pf_update(request, id):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(EmployeePF, id = id) 
        request.session['employee_pf'] = "update_pf"
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                if request.POST.get('status') == "on": request.POST["status"] = Status.name('active')
                else: request.POST["status"]  =Status.name('inactive')

                request.POST['employee'] = instance.employee
                request.POST['date_Pf_membership'] =datetime.strptime(request.POST.get('date_Pf_membership'), "%d-%b-%Y").date() if request.POST.get('date_Pf_membership') else ''
                form = EmpPfRegistationForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    request.session['employee_pf'] = None
                    message = 'Employee Pf Successfully Updated!'
                    messages.success(request, message)
                    return redirect("hr:pf_emp_enroll_list")
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                pf_list     = ProvidentFundMaster.objects.all()
                policy_list = PolicyMaster.objects.all()
                Pf_master = ProvidentFundMaster.objects.filter(status=True)
                action = {'name': 'Update', 'btnTxt': 'Update'}
                if request.session["role_text"].lower() in ["admin", "super admin", "user"]: 
                    employee_pf_list = EmployeePF.objects.all()
                else:
                    employee_pf_list = EmployeePF.objects.filter(company_id = request.session.get('company_id'))
                context = {
                    'option': "employee_pf_update",
                    'action'            : action,
                    'policy_list'       : policy_list,
                    'Pf_contribution'   : Pf_master,
                    'pf_instance'       : instance,
                    'employee_pf_list'  : employee_pf_list,
                    'pf_list'           : pf_list
                }
                return render (request, 'pf/pf_emp_create.html', context)
        else:   
            messages.warning(request,"PF details not found!")
            return redirect('hr:employee_pf_add')
    else:
        return redirect('/access-denied')

@login
def delete_employee_pf(request, id):
    chk_permission   = permission(request,"/hr/employee-add/")
    if chk_permission.delete_action:
        EmployeePF.objects.filter(id=id).delete()
        message = 'Employee Pf Deleted!'
        messages.success(request, message)
        return JsonResponse('Provident Fund Delete Successful.', safe=False)
    else:
        return JsonResponse('You have no access on this action!', safe=False)

@login
def pf_discontinue(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
            if request.method == 'POST':
                request.POST                = request.POST.copy()
                request.POST['employee_pf'] = request.POST.get('employee')
                form = PFDiscontinueForm (request.POST)
                if form.is_valid():
                    obj = form.save()
                    get_employee = EmployeePF.objects.filter(id=obj.employee_pf.id).last()
                    get_employee.status = Status.name('inactive')
                    get_employee.save()
                    message = ' Pf Discontinue Successful!'
                    messages.success(request, message)
                    if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                         pf_discontinue_list = PFDiscontinue.objects.all()
                    else:
                        pf_discontinue_list = PFDiscontinue.objects.filter(company_id = request.session.get('company_id'))
                    action = {'name': 'Add New', 'btnTxt': 'Submit'}
                    context = {
                        'option': "pf_discontinue_list",
                        'pf_discontinue_list' : pf_discontinue_list,
                        'action': action, 
                    }
                    return render(request, 'pf/pf_discontinue.html', context)
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                
                return redirect('hr:pf_discontinue')
            else:
                employee_pf_list   = EmployeePF.objects.filter(status = Status.name('active'))
                if request.session["role_text"].lower() in ["admin", "super admin"]: 
                    pf_discontinue_list = PFDiscontinue.objects.all()
                else:
                    pf_discontinue_list = PFDiscontinue.objects.filter(company_id = request.session.get('company_id'))
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    'pf_discontinue_list' : pf_discontinue_list,
                    'action': action, 
                    'employee_pf_list' : employee_pf_list,
                }
            return render(request, 'pf/pf_discontinue.html', context)
    else:
        return redirect('/access-denied')
    
@csrf_exempt
def get_pf_discontinue(request):  
    if request.POST.get('employee'):
        employee = EmployeePF.objects.filter(id=int(request.POST.get('employee'))).first()
        joining_date = employee.employee.joining_date
        pf_enroll_date = employee.date_Pf_membership
        to_date = datetime.now().date()
        date1 = datetime(joining_date.year, joining_date.month, joining_date.day)
        date2 = datetime(to_date.year, to_date.month, to_date.day)

        date3 = datetime(pf_enroll_date.year, pf_enroll_date.month, pf_enroll_date.day)
        date4 = datetime(to_date.year, to_date.month, to_date.day)
        diff  = relativedelta.relativedelta(date1, date2)
        diff2 = relativedelta.relativedelta(date3, date4)
        year = abs(int(diff.years)) 
        month = abs(int(diff.months))
        day = abs(int(diff.days))

        year1 = abs(int(diff2.years))
        month2 = abs(int(diff2.months))
        day3 = abs(int(diff2.days))
        tenure = str(year)+ " years "+str(month) + " month "+str(day)+" days"
        tenure2 = str(year1)+ " years "+str(month2) + " month "+str(day3)+" days"
        data = {
            'tenure2' : tenure2,
            'tenure' : tenure,
            'policy' :str(employee.policy),
            'status' : employee.status.title        
        }
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse("Something went wrong!", safe=False)

@login
def employee_transfer_log(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
            employee_transfer_list = EmployeeTransfer.objects.all()
        else:
            employee_transfer_list = EmployeeTransfer.objects.filter(employee__branch_id = request.session.get('branch_id'))

        company_list = Branch.objects.filter(status = True, company_id=request.session.get('company_id'))
        context = {
            'emp_transfer_log' : employee_transfer_list,
            'company_list' : company_list
        }
        return render(request, 'pf/employee_transfer_log.html', context)
    else:
        return redirect('/access-denied')

@csrf_exempt
def get_employee_transfer_list_filter(request):
    data_list = []
    search_text = request.POST.get('search_text','').strip()
    start       = int(request.POST.get('start', 0))
    company     = request.POST.get('company','')
    start_date  = request.POST.get('start_date', '')
    end_date    = request.POST.get('end_date', '') 
    if request.session["role_text"].lower() in ["admin", "super admin"]: 
        employee_transfer_list = EmployeeTransfer.objects.all()
    else:
        employee_transfer_list = EmployeeTransfer.objects.filter(employee__company_id = request.session.get('company_id'))


    if search_text: employee_transfer_list = employee_transfer_list.filter(Q(employee__employee_id__icontains=search_text)|Q(employee__name__icontains=search_text)|Q(employee__phone_no__icontains=search_text))

    if start_date or end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date + timedelta(days=1)
        employee_transfer_list = employee_transfer_list.filter(joining_date__gte=start_date, joining_date__lt=end_date)

    if company:  employee_transfer_list= employee_transfer_list.filter(employee__company_id = company)

    employee_transfer_list = employee_transfer_list[start:start + 20]
    for transfer in employee_transfer_list:
        employee = transfer.employee.employee_id if transfer.employee.employee_id else 'N/A'
        name     = transfer.employee.name if transfer.employee.name else 'N/A' 
        company  = transfer.employee.company.name if transfer.employee.company.name else 'N/A'
        department_from = transfer.department_from.name if transfer.department_from.name else 'N/A'
        department_to    = transfer.department_to.name if transfer.department_to.name else 'N/A'
        designation_from = transfer.designation_from.name if  transfer.designation_from.name else 'N/A'
        designation_to    = transfer.designation_to.name if transfer.designation_to.name else 'N/A'
        joining_date    = transfer.joining_date.strftime("%m/%d/%Y") if transfer.joining_date.strftime("%m/%d/%Y") else 'N/A'
        contact_number    = transfer.employee.phone_no if transfer.employee.phone_no else 'N/A'

        action =""  

        edit_url = reverse('hr:employee_pf_update', kwargs={'id': transfer.id})
        edit = '<a class="h4 m-r-10 text-success" href="' + edit_url + '" class="h4 text-danger" title="Update">'
        edit += '<span class="icon"><i class="ti-pencil-alt"></i></span></a>'
        action += edit
        data = [employee, name, company, department_from, department_to, designation_from,designation_to, joining_date, contact_number,action]
        data_list.append(data)

    return JsonResponse(data_list, safe=False)


@login
def employee_transfer(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
            if request.method == 'POST' and ebs_bl_common.is_ajax(request):
                if request.POST.get('submition_type') == 'save':
                    request.POST = request.POST.copy()
                    employee_info = EmployeeInfo.objects.filter(id=int(request.POST.get('emp_id'))).first()
                    request.POST["department_from"]      = employee_info.department.id
                    request.POST["designation_from"]    = employee_info.designation.id
                    request.POST["to_employee_id"]      = employee_info.employee_id
                    to_company                          = request.POST.get('company')
                    to_department                       = request.POST.get('department_to')
                    to_designation                      = request.POST.get('designation_to')
                    request.POST['effictive_from_date'] = datetime.strptime(request.POST.get('effictive_from_date'), "%d-%b-%Y").date() if request.POST.get('effictive_from_date') else ''

                    form = EmployeeTransferForm (request.POST)
                    if form.is_valid():
                        form.save()
                        employee_info.company = Company.objects.filter(id=int(to_company)).last()
                        employee_info.designation = Designations.objects.filter(id=int(to_department)).last()
                        employee_info.department = Departments.objects.filter(id=int(to_designation)).last()
                        employee_info.save()

                        message = ' Employee Successfully Transfer!'
                        data= {
                             "success": True,
                             "msg": message,
                             }
                        return JsonResponse (data, status=200)
                    else:
                        for field in form:
                            for error in field.errors:
                                messages.warning(request, "%s : %s" % (field.name, error))
                    return JsonResponse({"error": field.errors}, status=400)

                elif request.POST.get('submition_type') == 'submit':
                    request.POST = request.POST.copy()
                    request.POST['employee'] = int(request.POST.get('emp_id'))
                    instance = get_object_or_404(EmployeePF, id = int(request.POST.get('pf_emp_id')))
                    if int(request.POST.get('pf_id')) == int(request.POST["pf"]):
                        form = EmpPfRegistationForm(request.POST, instance=instance)
                        if form.is_valid():
                            message = ' Employee PF Imformation Successfully Updated!'
                            messages.success(request, message)
                            form.save()
                        return JsonResponse ({"success":True}, status=200)
                    else:
                        request.POST['status'] = Status.name('active')
                        form = EmpPfRegistationForm (request.POST)
                        if form.is_valid():
                            form.save()
                            EmployeePF.objects.filter(id = int(request.POST.get('pf_emp_id'))).update(status = Status.name('inactive'))
                            message = ' Employee PF Successfully Transfer!'
                            data= {
                                "success": True,
                                "msg": message,
                                }
                            
                            return JsonResponse (data, status=200)

                        else:
                            for field in form:
                                for error in field.errors:
                                    messages.warning(request, "%s : %s" % (field.name, error))
                        return JsonResponse({"error": form.errors}, status=400)
            else:
                employee_list      = EmployeeInfo.objects.all()
                company_list       = Branch.objects.filter(status = True, company_id=request.session.get('company_id'))
                department_list    = Departments.objects.filter(status=True)
                designation_list   = Designations.objects.filter(status=True)
                employee_pf_list   = EmployeePF.objects.filter(status=Status.name('active'))
                pf                 = ProvidentFundMaster.objects.all()
                policy             = PolicyMaster.objects.all()
                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                    employee_transfer_list = EmployeeTransfer.objects.all()
                else:
                    employee_transfer_list = EmployeeTransfer.objects.filter(employee__company_id = request.session.get('company_id'))
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    'action': action, 
                    'employee_transfer_list' : employee_transfer_list,
                    'employee_pf_list' : employee_pf_list,
                    'company_list'     : company_list,
                    'department_list'  : department_list,
                    'designation_list' : designation_list,
                    'employee_list'    : employee_list,
                    'pf'               : pf,
                    'policy'           : policy
                }
            return render(request, 'pf/employee_transfer.html', context)
    else:
        return redirect('/access-denied')

@csrf_exempt
def get_employee_transfer(request):
        if request.POST.get('employee'):
                employee = EmployeeInfo.objects.filter(id=int(request.POST.get('employee'))).first()
                pf = EmployeePF.objects.filter(employee_id=int(request.POST.get('employee'))).first()
                data = {
                    'emp_id' : employee.id,
                    'company' : str(employee.branch.name),
                    'employee' : employee.employee_id,
                    'father_name' : employee.father_name,
                    'permanent_address' : employee.permanent_address,
                    'contact_address' : employee.contact_address,
                    'email' : employee.email,
                    'department' : str(employee.department.name),
                    'designation' : str(employee.designation.name),
                    'phone' : employee.phone_no,
                    'fax' : employee.faxNo,
                    'policy' :pf.policy_id,
                    'joining_date' : employee.joining_date,
                    'basis_of_contribution' : pf.basis_of_contribution,
                    'input_basis_of_contribution' : pf.basis_of_contribution,
                    'basic_gross_salary' : str(pf.basic_gross_salary),
                    'date_Pf_membership' : str(pf.date_Pf_membership),
                    'rate_employee_contribution' : str(pf.rate_employee_contribution),
                    'rate_company_contribution' : str(pf.rate_company_contribution),
                    'emp_opening_contribution' : str(pf.emp_opening_contribution),
                    'company_opening_contribution' : str(pf.company_opening_contribution),
                    'emp_opening_balance_interest' : str(pf.emp_opening_balance_interest),
                    'company_opening_balance_interest' : str(pf.company_opening_balance_interest),
                    'pf_id'            : pf.pf_id,
                    'pf_emp_id'        : pf.id,
                }
                return JsonResponse(data, safe=False)
        else:
            return JsonResponse("Something went wrong!", safe=False)

@login
def pf_contribution_log(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
            emp_contribution_log = PFMonthlyContribution.objects.all()
        else:
            emp_contribution_log = PFMonthlyContribution.objects.filter(company_id = request.session.get('company_id'))

        conpany_list  = Branch.objects.filter(status = True, company_id=request.session.get('company_id'))
        pf_list       = ProvidentFundMaster.objects.all()
        context = {
            'conpany_list' : conpany_list,
            'pf_list'           : pf_list,
            'emp_contribution_log' : emp_contribution_log
        }
        return render(request, 'pf/pf_contribution_log.html', context)
    else:
        return redirect('/access-denied')

@csrf_exempt
def get_contribution_filter(request):
    data_list = []
    search_text = request.POST.get('search_text','').strip()
    start       = int(request.POST.get('start', 0))
    company     = request.POST.get('company','')
    pf          = request.POST.get('pf','')
    start_date  = request.POST.get('start_date', '')
    end_date    = request.POST.get('end_date', '') 
    if request.session["role_text"].lower() in ["admin", "super admin","users"]: 
        contribution_list = PFMonthlyContribution.objects.all()
    else:
        contribution_list = EmployeeTransfer.objects.filter(company_id = request.session.get('company_id'))


    if search_text: contribution_list = contribution_list.filter(Q(employee_pf__employee__employee_id__icontains=search_text)|Q(employee_pf__employee__name__icontains=search_text))

    if start_date or end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date + timedelta(days=1)
        contribution_list = contribution_list.filter(entry_date__gte=start_date, entry_date__lt=end_date)

    if company:  contribution_list= contribution_list.filter(employee_pf__employee__company = company)
    if pf:  contribution_list= contribution_list.filter(employee_pf__pf = pf)

    contribution_list = contribution_list[start:start + 20]
    for contribution in contribution_list:
        employee = contribution.employee_pf.employee.employee_id if contribution.employee_pf.employee.employee_id else 'N/A'
        name     = contribution.employee_pf.employee.name if contribution.employee_pf.employee.name else 'N/A' 
        company  = str(contribution.employee_pf.employee.company.name) if str(contribution.employee_pf.employee.company.name) else 'N/A'
        pf       = contribution.employee_pf.pf.pf_heading if contribution.employee_pf.pf.pf_heading else 'N/A'
        gross_salary = contribution.gross_salary if contribution.gross_salary else 'N/A'
        employee_rate = contribution.employee_pf.rate_employee_contribution if contribution.employee_pf.rate_employee_contribution else 'N/A'
        company_rate = contribution.employee_pf.rate_company_contribution if contribution.employee_pf.rate_company_contribution else 'N/A'
        contribution_amount = contribution.contribution_amount if contribution.contribution_amount else 'N/A'
        entry_date = contribution.entry_date.strftime("%m/%d/%Y") if contribution.entry_date.strftime("%m/%d/%Y") else 'N/A'
        action =""  

        edit_url = reverse('hr:employee_pf_update', kwargs={'id': contribution.id})
        edit = '<a class="h4 m-r-10 text-success" href="' + edit_url + '" class="h4 text-danger" title="Update">'
        edit += '<span class="icon"><i class="ti-pencil-alt"></i></span></a>'
        action += edit
        data = [employee, name, company,pf,gross_salary,employee_rate,company_rate,contribution_amount,entry_date,action]
        data_list.append(data)

    return JsonResponse(data_list, safe=False)
        
@login
def pf_contribution(request):
    chk_permission   = permission(request, "/hr/employee-add/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
            if request.method == 'POST':
                request.POST        = request.POST.copy()
                date = request.POST.get('entry_date').split('-')
                date_format = date[1]+'-'+date[0]+'-'+'01'
                pf_info = EmployeePF.objects.filter(pf_id=int(request.POST.get('pf')))
                msg = True
                for emp in pf_info :
                    emp_amount = company_amount = 0
                    if emp.rate_employee_contribution:
                        emp_amount = round((emp.employee.salary * emp.rate_employee_contribution)/100)
                    if emp.rate_company_contribution:
                        company_amount = round((emp.employee.salary * emp.rate_company_contribution)/100) 
                    total = emp_amount + company_amount
                    data = {
                        'employee_pf': emp.id,
                        'is_round': False,
                        'Voucher_no': 'ABC',
                        'emp_percent': emp.rate_employee_contribution,
                        'company_percent': emp.rate_company_contribution if emp.rate_company_contribution else 0,
                        'gross_salary': emp.basic_gross_salary,
                        'contribution_amount': total,
                        'created_by_id': request.session.get('id'),
                        'entry_date': datetime.strptime(date_format, '%Y-%m-%d'),
                        'month' : int(date[0]),
                        'year'  : int(date[1]),
                    }
                    form = PfContributionForm(data)
                    if form.is_valid():
                        obj=form.save()
                        obj.save()
                        message = 'PF Contribution Successfully Generate!'
                    else:
                        msg = False
                        message = 'PF Contribution Generate Faild!'
                if msg == True:
                    messages.success(request, message)
                else:
                    messages.warning(request, message)
                return redirect("hr:pf_contribution_log")
            else:
                pf_list   = ProvidentFundMaster.objects.filter(status = Status.name('active'))
                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                    pf_discontinue_list = PFMonthlyContribution.objects.all()
                else:
                    pf_discontinue_list = PFMonthlyContribution.objects.filter(company_id = request.session.get('company_id'))
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    'pf_discontinue_list' : pf_discontinue_list,
                    'action': action, 
                    'pf_list' : pf_list,
                }
                return render(request, 'pf/pf_contribution.html', context)
    else:
        return redirect('/access-denied')

@csrf_exempt
def get_contribution(request):
        pf = request.POST.get('pf')
        month_year = request.POST.get('entry_date').split('-') if request.POST.get('entry_date') else ''
        if pf and month_year:
            if PFMonthlyContribution.objects.filter(employee_pf__pf_id = pf, entry_date__month = month_year[0],entry_date__year = month_year[1]).exists():
                message = "Monthly Contribution Already Generated!"
                data = {
                     "success": True,
                     'msg' : message,
                     'icon': 'warning',
                }
                return JsonResponse (data, status=200)
            else:
                pf_employee_list = EmployeePF.objects.filter(pf_id=request.POST.get('pf'))
                emp_amount = company_amount = 0
                for emp in pf_employee_list:
                    if emp.rate_employee_contribution:
                        emp_amount += round((emp.employee.salary * emp.rate_employee_contribution)/100)
                    if emp.rate_company_contribution:
                        company_amount += round((emp.employee.salary * emp.rate_company_contribution)/100)
                data = {
                    'total_employee' : pf_employee_list.count(),
                    'emp_amount' : emp_amount,
                    'company_amount' : company_amount,
                    'success': False,
                    'msg' : '',
                    'icon': 'success',
                }
                return JsonResponse(data, safe=False)
        else:
            return JsonResponse("Something went wrong!", safe=False)

def import_employee_in_pf(request):
    chk_permission   = permission(request,request.path)
    if chk_permission and chk_permission.insert_action:
        if request.method == "POST":
            import_file = request.FILES['import_file']
            xl = pd.read_excel(import_file, "Sheet1") 
            new_count = 0
            for i in range(0,len(xl)):
                chk_emp = EmployeeInfo.objects.filter(employee_id = xl['Employee ID'][i])
                if chk_emp:
                    chk_pf_master = ProvidentFundMaster.objects.filter(pf_heading = xl['Provident Fund'][i])
                    joining_date = chk_emp[0].joining_date
                    to_date = datetime.now().date()
                    date1 = datetime(joining_date.year, joining_date.month, joining_date.day)
                    date2 = datetime(to_date.year, to_date.month, to_date.day)
                    diff = relativedelta.relativedelta(date1, date2)
                    year = abs(int(diff.years)) 
                    if year >= 1:
                        if chk_pf_master or chk_emp:
                            chk_pf  = EmployeePF.objects.filter(employee_id = chk_emp[0].id)
                            date= str(xl["PF Membership Date"][i]) if str(xl["PF Membership Date"][i]) != "nan" else ""
                            date_Pf = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date() if date else ''  #for converting date in valide formate
                            emp_opening_contribution = str(xl["Opening Balance of Employee's Contribution"][i]) if str(xl["Opening Balance of Employee's Contribution"][i]) != "nan" else "0"
                            company_opening_contribution = str(xl["Opening Balance of Company's Contribution"][i]) if str(xl["Opening Balance of Company's Contribution"][i]) != "nan" else "0"
                            emp_opening_balance_interest = str(xl["Opening Balance of Interest(Employee)"][i]) if str(xl["Opening Balance of Interest(Employee)"][i]) != "nan" else "0"
                            company_opening_balance_interest = str(xl["Opening Balance of Interest(Company)"][i]) if str(xl["Opening Balance of Interest(Company)"][i]) != "nan" else "0"
                            if year <= 3:
                                policy = PolicyMaster.objects.filter(effictive_year_from = ("1")).last()
                                pf = 0
                            else:
                                policy = PolicyMaster.objects.filter(effictive_year_from = ("3")).last()
                                pf = chk_pf_master[0].rate_company                
                            if chk_pf:
                                chk_pf.update(
                                    basis_of_contribution =xl ["Basis of PF Computation"][i],
                                    pf_id = chk_pf_master[0].id,
                                    emp_opening_contribution = emp_opening_contribution,
                                    company_opening_contribution = company_opening_contribution,
                                    emp_opening_balance_interest = emp_opening_balance_interest,
                                    company_opening_balance_interest = company_opening_balance_interest,
                                    basic_gross_salary = chk_emp[0].salary,
                                    policy_id = policy.id,
                                    rate_employee_contribution = chk_pf_master[0].rate_employee,
                                    rate_company_contribution = pf,
                                    date_Pf_membership = date_Pf,
                                )
                            else:
                                emp_pf_add = EmployeePF.objects.create(
                                    employee_id =  chk_emp[0].id,
                                    basis_of_contribution =xl ["Basis of PF Computation"][i],
                                    pf_id = chk_pf_master[0].id,
                                    emp_opening_contribution = emp_opening_contribution,
                                    company_opening_contribution = company_opening_contribution,
                                    emp_opening_balance_interest = emp_opening_balance_interest,
                                    company_opening_balance_interest = company_opening_balance_interest,
                                    basic_gross_salary = chk_emp[0].salary,
                                    policy_id = policy.id,
                                    rate_employee_contribution = chk_pf_master[0].rate_employee,
                                    rate_company_contribution = pf,
                                    date_Pf_membership = date_Pf,
                                    status = Status.name("Active")
                                )                                 
                                if emp_pf_add: new_count += 1 
                        else:
                            message = "Employee does not exist"
                            messages.warning(request, message)
                    else:
                        message = xl['Employee ID'][i]+" Employee Not Eligible"
                        messages.warning(request, message)  
                else:
                    message =  xl['Employee ID'][i]+" Employee Not Exist in Employee Table"
                    messages.warning(request, message)
            if new_count > 0:   
                messages.success(request,str(new_count)+" employees imported.")               
            return redirect('/hr/pf-emp-enroll-list/')  
        else:
            return render(request, 'pf/import_employee_in_pf.html')   
    else:
        return redirect('/access-denied')


@login
def separation_management(request):
    chk_permission   = permission(request, "/hr/separation-management/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        employee = EmployeeDetails.objects.filter(employee_id=request.session.get('employee_id')).first()
        if request.session["role_text"].lower() in ["admin", "super admin"] or request.session.get('department') == "HR, Admin & Compliance": 
            employee_list  = EmployeeInfo.objects.filter(status = True)
            pending_list   = EmployeeCessation.objects.filter(hr_admin__isnull = True)
            approved_list  = EmployeeCessation.objects.filter(hr_admin__isnull = False)
        else:
            employee_list  = EmployeeInfo.objects.filter(status = True)
            pending_list   = EmployeeCessation.objects.filter(hr_admin__isnull = True, emolpoyee_id = int(employee.id))
            approved_list  = EmployeeCessation.objects.filter(hr_admin__isnull = False, emolpoyee_id = int(employee.id))

        if request.method == 'POST': 
            request.POST               = request.POST.copy()
            request.POST['created_by'] = request.session.get("id")
            request.POST['emolpoyee']  = int(employee.id)
            date_str = request.POST.get('effective_from_date')  # This is a string
            if date_str: request.POST['effective_from_date'] = datetime.strptime(date_str, "%d-%b-%Y").date()
            else:request.POST['effective_from_date'] = None
            request.POST['letter_type'] = request.POST.get('letter_type') if request.session.get('department') == "HR, Admin & Compliance" else 1
            
            form = EmployeeCessationForm(request.POST, request.FILES)
            if form.is_valid():
                cessation=form.save()
                message = 'Successfully Added!'
                messages.success(request, message) 

                n_sender        = cessation.created_by
                n_action_url    = reverse('hr:separation_management')
                n_model         = 'Resignation'
                n_verb          = 'Resignation Submitted'
                n_description   = "A new resignation request has been submitted for review in HR."
                notify.send(n_sender, recipient=cessation.created_by.reporting_to, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
                return redirect(reverse('hr:separation_management'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error))
       
        action = {'name': 'Add New', 'btnTxt': 'Submit'}
        context = { 
            'action': action, 'pending_list':pending_list, 'employee_list' : employee_list, 'approved_list':approved_list
        }
        return render(request, 'hr/separation_management.html', context)
    else: return redirect('/access-denied')
 
def employee_cessation_action(request):
    cessation_id = request.POST.get('cessation_id')
    action_type = request.POST.get('action_type')
    comments = request.POST.get('hr_admin_comments')

    cessation = get_object_or_404(EmployeeCessation, id=cessation_id)
    cessation.hr_admin_id = int(request.session.get('id'))
    cessation.hr_admin_comments = comments
    from django.utils import timezone
    cessation.hr_admin_approved_at = timezone.now()
    user = get_object_or_404(Users, pk=request.session.get("id", ""))
    if action_type == 'approve':
        cessation.status_id = 3
        n_sender        = user
        n_action_url    = reverse('hr:separation_management')
        n_model         = 'Resignation'
        n_verb          = 'Resignation Approved'
        n_description   = "Your resignation request has been approved by HR."
        notify.send(n_sender, recipient=cessation.created_by, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
        
    elif action_type == 'reject':
        cessation.status_id = 5
        n_sender        = user
        n_action_url    = reverse('hr:separation_management')
        n_model         = 'Resignation'
        n_verb          = 'Resignation Rejected'
        n_description   = "Your resignation request has been rejected by HR."
        notify.send(n_sender, recipient=cessation.created_by, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
        
    cessation.save()
    return redirect('/hr/separation-management/')

@login
def promotion_demotion(request):
    chk_permission   = permission(request, "/hr/promotion-demotion/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        employee = EmployeeDetails.objects.filter(personal=request.POST.get('employee')).first()
        employee_list    = EmployeeInfo.objects.filter(status = True)
        promotion_list   = EmployeePromotionDemotion.objects.filter(status = True)
        designation_list = Designations.objects.filter(status=True).order_by('name')
        if request.method == 'POST': 
            request.POST               = request.POST.copy()
            request.POST['created_by'] = request.session.get("id")
            request.POST['employee']   = int(employee.id)
            request.POST['status']     = True
            request.POST['new_designation_id'] = int(request.POST.get('new_designation'))
            date_str   = request.POST.get('effective_date')
            if date_str: request.POST['effective_date'] = datetime.strptime(date_str, "%d-%b-%Y").date()
            else:request.POST['effective_date'] = None
            request.POST['action_type'] = request.POST.get('action_type')
            
            form = EmployeePromotionDemotionForm(request.POST)
            if form.is_valid(): 
                instance = form.save()
                instance.previous_designation = instance.employee.designation.name if instance.employee else ""
                instance.save()

                employee = instance.employee
                from_designation = employee.designation.name if employee.designation else ""
                old_salary = employee.salary if employee.salary else 0
                user_data = Users.objects.filter(employee_id = instance.employee.employee_id).last()
                # Save history
                PromotionDemotionHistory.objects.create(
                    record=instance,
                    changed_by=instance.created_by if instance.created_by else None,
                    action_type=instance.action_type,
                    from_designation=from_designation,
                    to_designation=instance.new_designation.name if instance.new_designation else "",
                    old_salary=old_salary,
                    increment_amount=instance.increment_amount,
                    new_salary=instance.new_salary,
                    effective_date=instance.effective_date,
                    remarks=instance.remarks
                )

                action_type = instance.action_type.lower()  # 'promotion' or 'demotion'
                if action_type == 'promotion':
                    message = 'Promotion Successfully Added!'
                    n_verb = 'Promotion Submitted'
                    n_description = "A new promotion has been submitted for review in HR."
                else:
                    message = 'Demotion Successfully Added!'
                    n_verb = 'Demotion Submitted'
                    n_description = "A new demotion has been submitted for review in HR."

                messages.success(request, message)
                n_sender        = instance.created_by
                n_action_url    = reverse('hr:promotion_demotion')
                n_model         = 'Promotion/Demotion'
                notify.send(n_sender, recipient=user_data, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
                return redirect(reverse('hr:promotion_demotion'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error))
        
        
        action = {'name': 'Add New', 'btnTxt': 'Submit'}
        context = { 
            'action': action, 'promotion_list':promotion_list, 'employee_list' : employee_list, 'designation_list':designation_list,
        }
        return render(request, 'hr/promotion_demotion.html', context)
    else: return redirect('/access-denied')

def promotion_history_view(request):
    employee_id = request.GET.get('employee_id')
    history = PromotionDemotionHistory.objects.filter(record__employee_id=employee_id).order_by('-effective_date')
    return render(request, 'hr/history_popup.html', {'history': history})

@login
def movement_registry(request):
    chk_permission   = permission(request, "/hr/separation-management/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        employee = EmployeeDetails.objects.filter(employee_id=request.session.get('employee_id')).first()
        if request.session["role_text"].lower() in ["admin", "super admin"] or request.session.get('department') == "HR, Admin & Compliance": 
            employee_list  = EmployeeInfo.objects.filter(status = True)
            pending_list   = EmployeeCessation.objects.filter(hr_admin__isnull = True)
            approved_list  = EmployeeCessation.objects.filter(hr_admin__isnull = False)
        else:
            employee_list  = EmployeeInfo.objects.filter(status = True)
            pending_list   = EmployeeCessation.objects.filter(hr_admin__isnull = True, emolpoyee_id = int(employee.id))
            approved_list  = EmployeeCessation.objects.filter(hr_admin__isnull = False, emolpoyee_id = int(employee.id))

        if request.method == 'POST': 
            request.POST               = request.POST.copy()
            request.POST['created_by'] = request.session.get("id")
            request.POST['emolpoyee']  = int(employee.id)
            date_str = request.POST.get('effective_from_date')  # This is a string
            if date_str: request.POST['effective_from_date'] = datetime.strptime(date_str, "%d-%b-%Y").date()
            else:request.POST['effective_from_date'] = None
            request.POST['letter_type'] = request.POST.get('letter_type') if request.session.get('department') == "HR, Admin & Compliance" else 1
            
            form = EmployeeCessationForm(request.POST, request.FILES)
            if form.is_valid():
                cessation=form.save()
                message = 'Successfully Added!'
                messages.success(request, message) 

                n_sender        = cessation.created_by
                n_action_url    = reverse('hr:separation_management')
                n_model         = 'Resignation'
                n_verb          = 'Resignation Submitted'
                n_description   = "A new resignation request has been submitted for review in HR."
                notify.send(n_sender, recipient=cessation.created_by.reporting_to, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
                return redirect(reverse('hr:separation_management'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error))
       
        action = {'name': 'Add New', 'btnTxt': 'Submit'}
        context = { 
            'action': action, 'pending_list':pending_list, 'employee_list' : employee_list, 'approved_list':approved_list
        }
        return render(request, 'hr/movment_registry.html', context)
    else: return redirect('/access-denied')
 

@login
def employee_transfer_branchwise(request):
    chk_permission   = permission(request, "/hr/employee-transfer-branchwise/")
    if chk_permission and chk_permission.view_action and chk_permission.insert_action:
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['created_by'] = request.session.get('id')
            employee    = request.POST.get('employee')
            selected_employee = Users.objects.filter(id=employee).last()
            request.POST['from_branch'] = selected_employee.branch if selected_employee else None
            request.POST['status']      = True
            form = EmployeeBranchTransferForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully add!")
                return redirect(reverse_lazy('hr:employee_transfer_branchwise'))
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/employee/transfer_list.html"
        object_list     = EmployeeBranchTransfer.objects.order_by('-id')
        action_url      = reverse_lazy('hr:employee_transfer_branchwise')
        action_name     = "Employee Branch Transfer"
        employee_list   = Users.objects.filter(status=True,branch__company_id=request.session.get('company_id'))
        branch_list     = Branch.objects.filter(status=True,company_id=request.session.get('company_id'))
        form            = EmployeeBranchTransferForm()
        context         = { 'action_name':action_name, 'form':form, 
                           'action_url':action_url, 'object_list':object_list,
                           'employee_list':employee_list,'branch_list':branch_list
                           }
        return render(request, template_name, context)
    else: return redirect('/access-denied')

@login
def employee_transfer_branchwise_update(request, id):
    chk_permission   = permission(request, "/hr/employee-transfer-branchwise/")
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        try:
            instance = get_object_or_404(EmployeeBranchTransfer, id=id)
            if request.method == "POST":
                request.POST = request.POST.copy()
                employee    = request.POST.get('employee')
                selected_employee = Users.objects.filter(id=employee).last()
                request.POST['from_branch'] = selected_employee.branch if selected_employee else None
                form = EmployeeBranchTransferForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                    return redirect(reverse_lazy('hr:employee_transfer_branchwise'))
                else : ebs_bl_common.form_errors(request, form)

            template_name   = "hr/employee/transfer_list.html"
            action_name     = "Update Employee Branch Transfer"
            action_url      = reverse_lazy('hr:employee_transfer_branchwise_update', kwargs={'id':id})
            object_list     = EmployeeBranchTransfer.objects.order_by('id')
            employee_list   = Users.objects.filter(status=True,branch__company_id=request.session.get('company_id'))
            branch_list     = Branch.objects.filter(status=True,company_id=request.session.get('company_id'))
            form            = EmployeeBranchTransferForm(instance=instance)

            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance, 'employee_list':employee_list,'branch_list':branch_list}
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('hr:employee_transfer_branchwise'))
    else: return redirect('/access-denied')
    

# this is the function for loan
try: from hr.view.loan import *
except ImportError: pass

# Complience Views
try: from hr.view.audit_views import *
except ImportError: pass
try: from hr.view.license_views import *
except ImportError: pass

from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()

def holiday_context():
    setup_list, yearly_setups, year = HolidaySetup.objects.all(), [], datetime.now().year
    
    return { 
        'company_list'  : Branch.objects.filter(status = True).order_by('name'),
        'months'        : [[m[0], m[1]] for m in HolidaySetup.month_list],
        'tab_name'      : 'holiday',
        'haction_name'  : "Add Holiday", 
        'hform'         : HolidayForm(), 
        'haction_url'   : reverse_lazy('hr:holiday_list'), 
        'holiday_list'  : Holiday.objects.filter(start_date__year=datetime.now().year, status=Status.name("active")).order_by('start_date'),
        'saction_name'  : "Add Entry", 
        'sform'         : HolidaySetupForm(),
        'saction_url'   : reverse_lazy('hr:holiday_setup_list'), 
        'setup_list'    : setup_list,
        'yearly_setups' : yearly_setups,
    }
# ============ HolidaySetup Start ============ #
try: from hr.view.holiday_setup import *
except ImportError: pass
# ============ HolidaySetup End ============ #
# ============ Holiday Start ============ #
try: from hr.view.holiday import *
except ImportError: pass
# ============ Holiday End ============ #



# ============ NoticeBoard Start ============ #
try: from hr.view.notice_board import *
except ImportError: pass
# ============ NoticeBoard End ============ #



# ============ Leave Type Start ============ #
try: from hr.view.leave_type import *
except ImportError: pass
# ============ Leave Type End ============ #
# ============ Leave Master Start ============ #
try: from hr.view.leave_master import *
except ImportError: pass
# ============ Leave Master End ============ #
# ============ Leave Allocation Start ============ #
try: from hr.view.leave_allocation import *
except ImportError: pass
# ============ Leave Allocation End ============ #
# ============ Leave Application Start ============ #
try: from hr.view.leave_application import *
except ImportError: pass
# ============ Leave Application End ============ #

# ============ Location Start ============ #
try: from hr.view.location import *
except ImportError: pass
# ============ Location End ============ #

# ============ Building Start ============ #
try: from hr.view.building import *
except ImportError: pass
# ============ Building End ============ #

# ============ Shift Start ============ #
try: from hr.view.shift import *
except ImportError: pass
# ============ Shift End ============ #

# ============ Employee Start ============ #
try: from hr.view.views_employee import *
except ImportError: pass
# ============ Employee End ============ #

# ============ Attendance Start ============ #
try: from hr.view.attendance import *
except ImportError: pass
# ============ Attendance End ============ #

# ============ Man Power Budget Start ============ #
try: from hr.view.views_mp_budget import *
except ImportError: pass
# ============ Man Power Budget End ============ #

# ============ Recruitment Start ============ #
try: from hr.view.views_recruitment import *
except ImportError: pass
# ============ Recruitment End ============ #

# ============ Salary Start ============ #
try: from hr.view.salary import *
except ImportError: pass
# ============ Salary End ============ #


# ============ HRSalaryCycle Start ============ #
try: from hr.view.hr_salary_cycle import *
except ImportError: pass
# ============ HRSalaryCycle End ============ #



# ============ HRFloor Start ============ #
try: from hr.view.hr_floor import *
except ImportError: pass
# ============ HRFloor End ============ #

# ============ Company Unit Start ============ #
try: from hr.view.company_unit import *
except ImportError: pass
# ============ Company Unit End ============ #

# ============ Salary Slabs/Heads Start ============ #
try: from hr.view.salary_slab_heads import *
except ImportError: pass
# ============ Salary Slabs/Heads End ============ #



# ============ HRAttendanceBonusRule Start ============ #
try: from hr.view.festival_bonus import *
except ImportError: pass
# ============ HRAttendanceBonusRule End ============ #



# ============ HRTiffinBillRule Start ============ #
try: from hr.view.hr_tiffin_bill_rule import *
except ImportError: pass
# ============ HRTiffinBillRule End ============ #


# ============ Loan Start ============ #
try: from hr.view.loans import *
except ImportError: pass
# ============ Loan End ============ #


# ============ Loan Start ============ #
try: from hr.view.appraisal import *
except ImportError: pass
# ============ Loan End ============ #



# ============ Division Start ============ #
try: from hr.view.division import *
except ImportError: pass
# ============ Division End ============ #



# ============ SubSection Start ============ #
try: from hr.view.sub_section import *
except ImportError: pass
# ============ SubSection End ============ #



# ============ FiscalYear Start ============ #
try: from hr.view.fiscal_year import *
except ImportError: pass
# ============ FiscalYear End ============ #
