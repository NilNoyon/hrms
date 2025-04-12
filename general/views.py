from django.db import connections
from django.shortcuts import render, redirect, get_object_or_404, reverse, resolve_url
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import *
from .forms import *
from django.contrib.auth.hashers import make_password
from django.template.defaultfilters import slugify
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Q
import ast, json, os, random, hashlib, pandas as pd, csv
from PIL import Image
from datetime import datetime, date, timedelta, timezone
from django.utils.dateformat import DateFormat
from general.decorators import login, permission
from django.contrib.sessions.models import Session
from hr.models import EmployeeInfo, EmployeeDetails
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse_lazy,reverse
from notification.models import Notification
from django.forms import model_to_dict
from notification.utils import id2slug, slug2id

def app_login(request):
    if request.session.get('id'):
        return redirect("dashboard")
    if request.method == 'POST':
        user = Users.objects.filter(employee_id=str(request.POST['employee_id']).upper(),  status=True)
        if user:
            md5_obj = hashlib.md5((request.POST['password']).encode())
            encripted_pass = md5_obj.hexdigest()
            if user.filter(password=encripted_pass):
                for s in Session.objects.filter(expire_date__date__gte = datetime.now().date()).order_by("-expire_date"):  # single login at a time for a single user
                    if 'id' in s.get_decoded() and user[0].id == s.get_decoded()["id"]:
                        Session.objects.filter(session_key=s.session_key).delete()
                try:
                    assert settings.CACHES
                    cache.close_caches()
                    cache.clear()
                except AttributeError : pass
                
                # ebs_bl_common.create_custom_session(user[0], request)
                try:
                    request.session['is_head']              = True if user[0].is_department_head else False
                    request.session['id']                   = user[0].id
                    request.session['employee_id']          = user[0].employee_id
                    request.session['name']                 = str(user[0].name)
                    request.session['email']                = user[0].email
                    request.session['role']                 = str(user[0].role)
                    request.session['role_text']            = str(user[0].role.name)
                    request.session['secondary_role']       = user[0].secondary_role if user[0].secondary_role else []
                    request.session['user_roles']           = request.session['secondary_role'] + [user[0].role.name]
                    request.session['secondary_company']    = user[0].secondary_company if user[0].secondary_company else []
                    request.session['branch_id_list']       = request.session['secondary_company'] + [user[0].branch_id]
                    request.session['company']              = str(user[0].branch.company.name)
                    request.session['company_id']           = str(user[0].branch.company_id)
                    request.session['branch_id']            = str(user[0].branch_id)
                    request.session['department']           = str(user[0].department.name)
                except Exception as e:
                    messages.warning(request, str(e))
                    return render(request, "login1.html",{"employee_id":request.POST['employee_id']})
                try:
                    employee_info = EmployeeInfo.objects.get(employee_id=user[0].employee_id)
                    request.session['photo']        = str(employee_info.photo) if employee_info.photo else ''
                    request.session['emp_email']    = str(employee_info.email) if employee_info.email else False
                    request.session['emp_phone']    = str(employee_info.phone_no) if employee_info.phone_no else False
                except EmployeeInfo.DoesNotExist : request.session['photo'] = ''
                
                messages.success(request, "Login Successful.")
                next_url = request.POST.get("next_url")
                return redirect("dashboard") if not next_url else redirect(next_url)
            else:
                messages.warning(request, "Invalid password!")
                return render(request, "login1.html",{"employee_id":request.POST['employee_id']})
        else:
            messages.warning(request, "Invalid employee ID!")
            return render(request, "login1.html",{"employee_id":request.POST['employee_id']})

    return render(request, "login1.html")


@login
def app_logout(request):
    try:
        for s in Session.objects.all().order_by("-expire_date"):  # delete session data
            if 'id' in s.get_decoded() and request.session.get('id') == s.get_decoded()["id"]:
                Session.objects.filter(session_key=s.session_key).delete()
                break
    except : pass 
    messages.success(request, "Logout Successful.")
    return redirect("/")

@login
def dashboard(request):
    # try:
        from django.utils import timezone
        # menu = UserPermission.objects.filter(employee_id=request.session.get('employee_id'))
        try:
            # to clear cache use this
            from django.core.cache import cache
            cache.clear()
        except: pass

        # For Dashboard Reports
        hide_bulleting_data = True

        # For Users & Notification
        user            = Users.objects.get(id=request.session.get('id'))
        total_user      = Users.objects.filter(status=True).count()
        active_users    = Session.objects.filter(expire_date__gte=timezone.now())
        notifications   = Notification.objects.filter(recipient=user)
        unread_list     = []
        
        # For Quick Links
        # access_list = []
        access_list = UserPermission.objects.filter(user_id = request.session.get('id')).order_by("menu__module_name")

        for notification in notifications.unread():
            struct = model_to_dict(notification)
            struct['slug'] = id2slug(notification.id)
            if notification.actor:
                struct['actor'] = str(notification.actor)
            if notification.target:
                struct['target'] = str(notification.target)
            if notification.action_object:
                struct['action_object'] = str(notification.action_object)
            struct['timesince'] = notification.timesince()
            struct['slug'] = notification.slug
            unread_list.append(struct)

        context = {
            'unread_count': notifications.unread().count(),
            'unread_list': unread_list,
            'user': user, 
            'total_user' :total_user,
            'active_users': active_users,
            'access_list': access_list,
            'is_bulletin_data': False,
        }
        return render(request, 'home1.html', context )
    # except Exception as e:
    #     messages.warning(request,str(e))
    #     return render(request, 'home2.html' )
     

def sewing_dashboard(request):
    return render(request, "sewing_dashboard.html")

def assignZeroToNoneObj(operation_bulletin): #obj input (due to avoid none type error in dashboard
    operation_bulletin.efficiency_day_plan = 0
    operation_bulletin.efficiency_day = 0
    operation_bulletin.efficiency_mtd_plan = 0
    operation_bulletin.efficiency_mtd = 0
    operation_bulletin.fob_day_plan = 0
    operation_bulletin.fob_day = 0
    operation_bulletin.fob_mtd_plan = 0
    operation_bulletin.fob_mtd = 0
    operation_bulletin.foc_day_plan = 0
    operation_bulletin.foc_day = 0
    operation_bulletin.foc_mtd_plan = 0
    operation_bulletin.foc_mtd = 0
    operation_bulletin.cm_day_plan = 0
    operation_bulletin.cm_day = 0
    operation_bulletin.cm_mtd_plan = 0
    operation_bulletin.cm_mtd = 0
    operation_bulletin.inspect_fob_day_plan = 0
    operation_bulletin.inspect_fob_day = 0
    operation_bulletin.inspect_fob_mtd_plan = 0
    operation_bulletin.inspect_fob_mtd = 0
    operation_bulletin.ship_fob_day_plan = 0
    operation_bulletin.ship_fob_day = 0
    operation_bulletin.ship_fob_mtd_plan = 0
    operation_bulletin.ship_fob_mtd = 0
    return operation_bulletin

from django.core.cache import cache, caches
@csrf_exempt
@login
def get_dashboard_info(request):
    try:
        report_date = request.POST.get('date')
        dashboard_report_date = cache.get('dashboard_report_date')
        if report_date == dashboard_report_date:
            dashboard_reports = cache.get('dashboard_reports')
            if dashboard_reports: 
                return render(request, 'home_info.html', dashboard_reports)
        date = datetime.strptime(report_date, "%b %d, %Y")
        return render(request, 'home_info.html')
    except Exception as e:
        messages.warning(request, str(e))
        return render(request, 'home_info.html')

@login
def logged_users(request):
    from django.utils import timezone
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now()).order_by("-expire_date")
    user_list = ""
    for session in active_sessions:
        data = session.get_decoded()
        if data and data.get('id'):
            # expire_date = datetime.strftime(session.expire_date,"%Y-%m-%d, %I:%M:%S %p")
            session_start = (session.expire_date - timedelta(seconds=settings.SESSION_COOKIE_AGE))
            user_session = CustomSession.objects.filter(user_id=data["id"]).last()
            # if session.ip_address: ip_address = session.ip_address
            # if session.local_ip_address: ip_address += "("+str(session.local_ip_address)+")"
            user_list += """
                <tr>
                    <td>"""+str(data["employee_id"])+"""</td>
                    <td><a href="#aboutModal" data-toggle="modal" data-id='"""+str(data["id"])+"""' class='user_info' data-target="#myModal">"""+str(data["name"])+"""</a></td>
                    <td>"""+str(data["company_short_name"])+"""</td>
                    <td>"""+str(data["department"])+"""</td>
                    <td>"""+str(data["role_text"])+"""</td>
                    <td>"""+str(datetime.strftime(session_start, "%d-%b-%Y %I:%M %p").upper())+"""</td>
                    <td>"""+str((user_session.local_ip_address or "") if user_session else "")+"""</td>
                    <td>"""+str((user_session.mac_address or "") if user_session else "")+"""</td>
                </tr>
            """

    context = {
        "user_list":user_list
    }
    return render(request, 'logged_users.html', context)

@csrf_exempt
def update_ip(request):
    user_session = CustomSession.objects.filter(user_id=request.POST.get('user', None)).last()
    if ip_address := request.POST.get('ip', None) : user_session.local_ip_address = ip_address
    user_session.save()
    return JsonResponse({}, safe=False)


@login
def version(request):
    return render(request, "version.html")

def form(request):
    return render(request, "form.html")

def table(request):
    return render(request, "table.html")
# -----------user start-----------


@login
def teams(request):
    return render(request, "teams.html")

@login
def analytics_reports(request):
    return render(request, "analytics_reports.html")

@login
def user_index(request):
    chk_permission   = permission(request, reverse("user_index"))
    if chk_permission and chk_permission.view_action:
        if request.session["role_text"] == "Admin" or request.session["role_text"] == "Super Admin":
            user_list = Users.objects.all().exclude(employee_id = 'admin')
            submitted_count   = Users.objects.all().exclude(employee_id = 'admin').count()
            # active_count   = Users.objects.filter(status = True).exclude(employee_id = 'admin').count()
            dept_list = Departments.objects.all()
            role_list = UserRoles.objects.all()
            context = {
                'user_list':user_list,
                'dept_list':dept_list,
                'role_list':role_list,
                'submitted_count':submitted_count,
                # 'active_count':active_count,
            }
            return render(request, 'user/index_v2.html', context)
        else: return redirect('/')
    else:
        return redirect('/access-denied')

@csrf_exempt
# def get_users_for_dataTable(request):
#     data_list = []
#     search_text = request.POST.get('search[value]', '')
#     start = int(request.POST.get('start', 0))
#     user_list = Users.objects.all().exclude(employee_id = 'admin')
    
#     if search_text:
#         user_list = user_list.filter(
#                         Q(name__icontains=search_text) 
#                         | Q(employee_id__icontains=search_text)
#                         | Q(department__name__icontains=search_text)
#                         | Q(designation__name__icontains=search_text)
#                         | Q(reporting_to__name__icontains=search_text)
#                         | Q(role__name__icontains=search_text)
#                     )

#     user_list = user_list[start:start+20]

#     for user in user_list:
#         name = user.name[:25] + ('...' if len(user.name) > 25 else '')
#         department = user.department.name[:15] + ('...' if len(user.department.name) > 15 else '') if user.department_id else ''
#         designation = user.designation.name if user.designation_id else ''
#         reporting_to = user.reporting_to.name[:25] + ('...' if len(user.reporting_to.name) > 25 else '') if user.reporting_to_id else ''
#         role = user.role.name if user.role_id else ''
#         status = '<label class="mx-auto"><input type="checkbox" data-id="'+str(user.id)+'" '
#         status += 'checked' if user.status == 1 else ''
#         status += ' name="status" class="js-switch user-update-switch" data-color="#009efb" data-size="mini" /></label>'
#         edit_url = reverse("user_edit", kwargs={'id':user.id})
#         action = '<a href="'+edit_url+'" class="h4 m-r-10 text-success"><span class="icon"><i class="ti-pencil-alt"></i></span></a>'
#         action += '<a href="#" data-id="'+str(user.id)+'" class="h4 m-r-10 text-danger resetPass"><span class="icon"><i class="fas fa-sync"></i></span></a>'
#         data = [user.employee_id, name, department, designation, reporting_to, role, status, action]
#         data_list.append(data)

#     return JsonResponse(data_list, safe=False)

@csrf_exempt
def get_users_for_dataTable(request,status):
    chk_permission   = permission(request, reverse("user_index"))
    if chk_permission and chk_permission.view_action:
        query           = Q()
        user           = request.POST.get("user")
        dept           = request.POST.get("dept")
        role           = request.POST.get("role")

        if status == "submitted": #submitted tab
            user_id = request.session.get('id')
            # if company: query &= Q(allocation_master__fabric_order__pre_cost__company_id=company)
            if user: query &= Q(employee_id = user)
            if dept: query &= Q(department_id = dept)
            if role: 
                roles = UserRoles.objects.filter(id=role).first()
                if roles: query &= Q(Q(role_id = role)|Q(secondary_role__icontains = roles.name))
                else: query &= Q(role_id = role)
            search_text     = request.POST.get('search_text', '').strip()
            if search_text:
                query &= (Q(name__icontains=search_text) 
                           | Q(designation__name__icontains=search_text)
                           | Q(company__name__icontains=search_text)
                            )
                
            start   = int(request.POST.get('start', 0))
            query_data_list = Users.objects.filter(query).exclude(employee_id = 'admin').order_by('name')[start:start+20]   
            data_list = []
            for count, user in enumerate(query_data_list):
                name = user.name[:25] + ('...' if len(user.name) > 25 else '')
                department = user.department.name[:15] + ('...' if len(user.department.name) > 15 else '') if user.department_id else ''
                designation = user.designation.name if user.designation_id else ''
                reporting_to = user.reporting_to.name[:25] + ('...' if len(user.reporting_to.name) > 25 else '') if user.reporting_to_id else ''
                role = user.role.name if user.role_id else ''
                status = '<label class="mx-auto"><input type="checkbox" data-id="'+str(user.id)+'" '
                status += 'checked' if user.status == 1 else ''
                status += ' name="status" class="js-switch user-update-switch" data-color="#009efb" data-size="mini" /></label>'
                edit_url = reverse("user_edit", kwargs={'id':user.id})
                action = '<a href="'+edit_url+'" class="h4 m-r-10 text-success"><span class="icon"><i class="ti-pencil-alt"></i></span></a>'
                action += '<a href="#" data-id="'+str(user.id)+'" class="h4 m-r-10 text-danger resetPass"><span class="icon"><i class="fas fa-sync"></i></span></a>'
                data = [user.employee_id, name, department, designation, reporting_to, role, status, action]
                data_list.append(data)
             
            return JsonResponse(data_list, safe=False)
              
    else:
        data = {
            "msg":"You have no permission on this action!",
            "icon":"warning"
        }
        return JsonResponse(data, safe=False)

@login
def addUser(request):
    chk_permission   = permission(request,reverse("addUser"))
    if chk_permission and chk_permission.insert_action:
        if request.session["role_text"] == "Admin" or request.session["role_text"] == "Super Admin": 
            syncUsers(request) #user update from employee info
            # generated encryption pass :
            # text = admin
            # pass = 21232f297a57a5a743894a0e4a801fc3
            if request.method == 'POST':
                request.POST = request.POST.copy()
                if request.POST.get('status') == 'on':
                    request.POST['status'] = 1
                else:
                    request.POST['status'] = 0

                md5_obj = hashlib.md5(request.POST.get("employee_id").encode())
                encripted_pass = md5_obj.hexdigest()
                request.POST['password_text'] = request.POST.get("employee_id")
                request.POST['password'] = encripted_pass
                request.POST['secondary_role'] = request.POST.getlist('secondary_role')
                request.POST['secondary_company'] = [int(i) for i in request.POST.getlist('secondary_company')] if request.POST.getlist('secondary_company') and len(request.POST.getlist('secondary_company')) > 0 else []
                form = UserAddForm(request.POST)
                # return HttpResponse(form)
                if form.is_valid():
                    form.save()
                    message = request.POST.get('name')+' - User Successfully Added!'
                    messages.success(request, message)
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                return redirect('user_index')
            else:
                dept_head_list = Users.objects.filter(status=True)
                company_list = Company.objects.filter(status=True)
                department_list = Departments.objects.filter(status=True)
                designation_list = Designations.objects.filter(status=True)
                role_list = UserRoles.objects.filter(status=True)
                user = {'status': 1}
                action = {'name': 'Insert', 'btnTxt': 'Submit'}
                context = {
                    'action': action, 'user': user,
                    'dept_head_list': dept_head_list,
                    'department_list': department_list,
                    'designation_list': designation_list,
                    'company_list': company_list,
                    'secondary_company_list': company_list,
                    'role_list': role_list,
                }
            return render(request, 'user/form.html', context)
        else: return redirect('/')
    else:
        return redirect('/access-denied')

@login
def company(request):
    chk_permission   = permission(request,reverse("company"))
    if chk_permission and chk_permission.insert_action: 
        if request.method == 'POST':
            request.POST = request.POST.copy()
            form = CompanyForm(request.POST) 
            if form.is_valid():
                form.save()
                message = request.POST.get('short_name')+' - Company Successfully Added!'
                messages.success(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error)) 
        user_list      = Users.objects.filter(status=True) 
        company_list   = Company.objects.order_by('-id')
        banks          = Bank.objects.order_by('name')
        context = { 
            'user_list'    : user_list, 
            'company_list' : company_list, 
            'banks'        : banks, 
            'action_name'  : "Submit", 
            'tab_name'     : "Add Company", 
        }
        return render(request, 'company.html', context)
             
    else:
        return redirect('/access-denied')

@login
def update_company(request, id):
    chk_permission   = permission(request,reverse("company"))
    if chk_permission.update_action: 
        instance = get_object_or_404(Company, id=id)
        if request.method == 'POST':
            request.POST = request.POST.copy()
            if request.POST.get('status') == 'on': request.POST['status'] = 1
            else: request.POST['status'] = 0

            form = CompanyForm(request.POST, instance=instance) 
            if form.is_valid():
                company = form.save()
                company.weekends = request.POST.getlist('weekends', [])
                company.save()
                message = company.short_name + ' - Company Successfully Updated!'
                messages.success(request, message)
                return redirect('/user/company/')
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error)) 
        user_list      = Users.objects.filter(status=True) 
        company_list   = Company.objects.order_by('-id') 
        banks          = Bank.objects.order_by('name')
        context = { 
            'user_list'       : user_list, 
            'company_list'    : company_list, 
            'banks'           : banks, 
            'instance'        : instance, 
            'action_name'     : "Update", 
            'tab_name'        : "Update Company", 
        }
        return render(request, 'company.html', context)
             
    else:
        return redirect('/access-denied')
@login
def delete_company(request, id):
    chk_permission   = permission(request,reverse("company"))
    if chk_permission.delete_action:
        Company.objects.filter(id=id).delete()
        return JsonResponse('Company Delete Successful.', safe=False)
    else:
        return JsonResponse('You have no access on this action!', safe=False)
 
@login
def syncUsers(request):
    try:
        #for updating and creating new user from employee table
        employee_list = EmployeeInfo.objects.raw("SELECT * FROM public.employee_info e where employee_id not in(select employee_id from public.users)")
        if len(employee_list) > 0:
            for u in EmployeeDetails.objects.all().distinct('department'):
                if not Departments.objects.filter(name=u.department) and u.department: Departments.objects.create(name = u.department)

            for u in EmployeeDetails.objects.all().distinct('designation'):
                if not Designations.objects.filter(name=u.designation) and u.designation: Designations.objects.create(name = u.designation)

            user_role = UserRoles.objects.filter(name='User').first()
            if not user_role: user_role = UserRoles.objects.create(name='User')
            
            for u in employee_list:
                md5_obj = hashlib.md5(u.employee_id.encode())
                encripted_pass = md5_obj.hexdigest() 
                ed = EmployeeDetails.objects.filter(personal=u).first()
                if ed :
                    company     = Company.objects.filter(Q(name=ed.company)|Q(short_name=ed.company)).first()
                    department  = Departments.objects.filter(name=ed.department).first()
                    designation = Designations.objects.filter(name=ed.designation).first()

                if not Users.objects.filter(employee_id=u.employee_id):
                    report_to = Users.objects.filter(employee_id=ed.reporting_to).first()
                    if report_to: report_to = report_to.id
                    Users.objects.create(company_id=company.id, department_id=department.id, name=u.name, email=u.email,
                        designation_id=designation.id, password=encripted_pass, password_text=u.employee_id, 
                        employee_id=u.employee_id.strip(), role_id=user_role.id, reporting_to_id=report_to)  
        
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
def user_update(request, id):
    chk_permission   = permission(request, reverse("user_index"))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(Users, id=id)
        if request.method == 'POST':
            request.POST = request.POST.copy()
            if request.POST.get('status') == 'on':
                request.POST['status'] = 1
            else:
                request.POST['status'] = 0
            request.POST['password'] = instance.password
            request.POST['password_text'] = instance.password_text
            request.POST['secondary_role'] = request.POST.getlist('secondary_role')
            request.POST['secondary_company'] = [int(i) for i in request.POST.getlist('secondary_company')] if request.POST.getlist('secondary_company') and len(request.POST.getlist('secondary_company')) > 0 else []
            form = UserAddForm(request.POST, instance=instance)
            # return HttpResponse(form)
            if form.is_valid():
                form.save()
                message = instance.name+' - User Successfully Updated!'
                messages.success(request, message)
                if not instance.status:
                    for s in Session.objects.all().order_by("-expire_date"):  # delete session data
                        if 'id' in s.get_decoded() and id == s.get_decoded()["id"]:
                            Session.objects.filter(session_key=s.session_key).delete()
                            break
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error))
        else:
            dept_head_list = Users.objects.filter(status=True)
            company_list = Branch.objects.filter(status=True,company=instance.branch.company)
            department_list = Departments.objects.filter(status=True)
            designation_list = Designations.objects.filter(status=True)
            role_list = UserRoles.objects.filter(status=True)
            user = instance
            action = {'name': 'Update', 'btnTxt': 'Update'}
            context = {
                'action': action, 'user': user,
                'dept_head_list': dept_head_list,
                'department_list': department_list,
                'designation_list': designation_list,
                'company_list': company_list,
                'secondary_company_list': company_list.exclude(id = instance.branch_id),
                'role_list': role_list,
            }
            return render(request, 'user/form.html', context)
        return redirect('user_index')
    else:
        return redirect('/access-denied')

@login
def myProfile(request):
    instance = get_object_or_404(EmployeeInfo, employee_id=request.session.get('employee_id'))
    if request.method == 'POST':
        request.POST = request.POST.copy()

        emp_photo = str(instance.photo) if instance.photo else ""
        if bool(request.FILES.get('photo', False)) == True:
            if instance.photo and os.path.exists("/assets/uploads/employees"+str(request.session.get('employee_id'))+".png"):
                os.remove("/assets/uploads/employees"+str(request.session.get('employee_id'))+".png")

            emp_photo = request.FILES['photo']

            if not os.path.exists(str(settings.MEDIA_ROOT)+'/employees/'):
                os.mkdir(str(settings.MEDIA_ROOT)+'/employees/')

            size = (200, 200)
            im = Image.open(emp_photo).convert('RGB')
            im.thumbnail(size)
            im.save(str(settings.MEDIA_ROOT)+"/employees/" +
                    str(request.session.get('employee_id'))+".png", format="PNG", quality=80)
            emp_photo = "/employees/" + str(request.session.get('employee_id'))+".png"
            request.session['photo'] = emp_photo
        instance.photo = emp_photo
  
        signature = str(instance.signature) if instance.signature else ""
        if bool(request.FILES.get('signature', False)) == True:
            if instance.signature and os.path.exists("/assets/uploads"+str(instance.signature)):
                os.remove("/assets/uploads"+str(instance.signature))

            signature = request.FILES['signature']

            if not os.path.exists(str(settings.MEDIA_ROOT)+'/employees_sign/'):
                os.mkdir(str(settings.MEDIA_ROOT)+'/employees_sign/')

            file_extnsn = str(str(signature).split(".")[1].lower())
            default_storage.save(str(settings.MEDIA_ROOT)+"/employees_sign/" +str(request.session.get('employee_id'))+"."+file_extnsn, ContentFile(signature.read()))
            signature = "/employees_sign/" + str(request.session.get('employee_id'))+"."+file_extnsn
        instance.signature = signature

        date_of_birth = request.POST.get('date_of_birth', '')
        request.POST['date_of_birth']= datetime.strptime(date_of_birth, "%d/%m/%Y")
        form = MyProfileUpdate(request.POST, instance=instance)
        if form.is_valid():
            if 'email' in request.POST:
                Users.objects.filter(employee_id=request.session.get('employee_id')).update(
                    email=request.POST.get("email"))
            form.save()
            if not request.session.get('emp_email') and request.POST.get("email"): request.session['emp_email'] = str(request.POST.get("email"))
            if not request.session.get('emp_phone') and request.POST.get("phone"): request.session['emp_phone'] = str(request.POST.get("phone"))
            messages.success(request, 'My Profile Successfully Updated.')
            return redirect(request.META.get('HTTP_REFERER'))

        else:
            for field in form:
                for error in field.errors:
                    messages.warning(request, "%s : %s" % (field.name, error))

    context = { 'user': instance, 'blood_group_list' : EmployeeInfo.group_type,
        'marital_status_list': CommonMaster.objects.filter(value_for=6), 
        'gender_list'   : CommonMaster.objects.filter(value_for=7),
        'religion_list' : CommonMaster.objects.filter(value_for=3)}
    return render(request, 'user/my_profile.html', context)
    
@login
def changePassword(request):
    if request.method == 'POST':
        md5_obj = hashlib.md5((request.POST['old_password']).encode())
        encripted_pass = md5_obj.hexdigest()
        user = Users.objects.filter(employee_id=request.session.get(
            'employee_id'),  password=encripted_pass, status=True)
        if user:
            if request.POST['new_password1'] == request.POST['new_password2']:
                md5_obj = hashlib.md5((request.POST['new_password1']).encode())
                encripted_pass = md5_obj.hexdigest()
                user.update(password=encripted_pass,
                            password_text=request.POST['new_password1'])
                message = 'Password Successfully Changed'
                messages.success(request, message)
            else:
                message = 'New and Re-type Password Did Not Matched!'
                messages.error(request, message)
        else:
            message = 'Current Password Did Not Matched!'
            messages.error(request, message)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request, 'user/change-password.html')

@csrf_exempt
@login
def updateStatus(request):
    chk_permission   = permission(request, reverse("user_index"))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(Users, id=request.POST.get('id'))
        if instance.status == 0:
            instance.status = 1
        else:
            instance.status = 0
            for s in Session.objects.all().order_by("-expire_date"):  # delete session data
                if 'id' in s.get_decoded() and instance.id == s.get_decoded()["id"]:
                    Session.objects.filter(session_key=s.session_key).delete()
                    break
        instance.save()
        return HttpResponse(instance.status)
    else:
        return HttpResponse('You have no access on this action!')

# ---------user end----------
import os
from django.conf import settings

@login
def user_access_control_setup(request):
    chk_permission   = permission(request, reverse("user_access_control_setup"))
    if chk_permission and chk_permission.view_action:
        # this is use for sync menulist from excel file
        #To read multiple sheet at once just follow this link, code needs to be change
        #https://pythoninoffice.com/read-multiple-excel-sheets-with-python-pandas/
        
        import_file =  open(os.path.join(settings.BASE_DIR, "assets/MenuList.xlsx"), "rb")
        xl = pd.ExcelFile(import_file, engine='openpyxl') 

        for sheet in xl.sheet_names:
            df  = pd.read_excel(import_file, sheet, engine='openpyxl')
            for i in range(0,len(df)):
                if str(df['URL'][i]) != 'nan' :
                    chk_menu = MenuList.objects.filter(menu_url = df['URL'][i].strip())
                    if not chk_menu:
                        sub_menu_name, menu_icon = "", ""
                        is_sub_menu = True if str(df["Is Sub Menu"][i]).lower() == 'yes' else False
                        if str(df["Icon"][i]) != 'nan': menu_icon = str(df["Icon"][i])
                        if str(df["Sub Menu Name"][i]) != 'nan': sub_menu_name = str(df["Sub Menu Name"][i]).title()
                        MenuList.objects.create(
                            module_name = sheet, menu_name =  df["Menu Name"][i].strip(), menu_url = df["URL"][i].strip(), menu_order = df["Ordering"][i],
                            menu_icon = menu_icon, sub_menu_name = sub_menu_name, is_sub_menu = is_sub_menu
                        )

        if ebs_bl_common.is_ajax(request):
            user_prev_list = json.loads(request.POST.get('user_prev_list'))
            user_id        = request.POST.get('user_id')
            user_role      = request.POST.get('user_role')
            designation    = request.POST.get('designation')
            department     = request.POST.get('department')
            company        = request.POST.get('company')
            menu_id_list   = [int(i['menu_id']) for i in user_prev_list]

            for data in user_prev_list:                    
                menu_id        = data['menu_id']
                view_action    = data['view_action']
                insert_action  = data['insert_action']
                update_action  = data['update_action']
                delete_action  = data['delete_action']
                if user_id and not user_role and not designation and not department:
                    chk_exist = UserPermission.objects.filter(user_id = user_id, menu_id = menu_id)
                    if chk_exist:
                        chk_exist.update(view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                    else:
                        UserPermission.objects.create(user_id = user_id, menu_id = menu_id, view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                elif not user_id and user_role and not designation and not department:
                    user_list = Users.objects.filter(role_id = user_role)
                    for emp in user_list:
                        chk_exist = UserPermission.objects.filter(user_id = emp.id, menu_id = menu_id)
                        if chk_exist:
                            chk_exist.update(view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                        else:
                            UserPermission.objects.create(user_id = emp.id, menu_id = menu_id, view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                elif not user_id and not user_role and designation and not department:
                    user_list = Users.objects.filter(designation_id = designation)
                    for emp in user_list:
                        chk_exist = UserPermission.objects.filter(user_id = emp.id, menu_id = menu_id)
                        if chk_exist:
                            chk_exist.update(view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                        else:
                            UserPermission.objects.create(user_id = emp.id, menu_id = menu_id, view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                elif not user_id and not user_role and not designation and department:
                    user_list = Users.objects.filter(department_id = department)
                    for emp in user_list:
                        chk_exist = UserPermission.objects.filter(user_id = emp.id, menu_id = menu_id)
                        if chk_exist:
                            chk_exist.update(view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                        else:
                            UserPermission.objects.create(user_id = emp.id, menu_id = menu_id, view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                elif not user_id and not user_role and designation and department:
                    user_list = Users.objects.filter(designation_id = designation, department_id = department)
                    for emp in user_list:
                        chk_exist = UserPermission.objects.filter(user_id = emp.id, menu_id = menu_id)
                        if chk_exist:
                            chk_exist.update(view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                        else:
                            UserPermission.objects.create(user_id = emp.id, menu_id = menu_id, view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                elif company and not user_id and not user_role and not designation and not department:
                    user_list = Users.objects.filter(company_id = company)
                    for emp in user_list:
                        chk_exist = UserPermission.objects.filter(user_id = emp.id, menu_id = menu_id)
                        if chk_exist:
                            chk_exist.update(view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                        else:
                            UserPermission.objects.create(user_id = emp.id, menu_id = menu_id, view_action = view_action, insert_action = insert_action, update_action = update_action, delete_action = delete_action)
                    UserPermission.objects.filter(user_id = emp.id).exclude(menu_id__in = menu_id_list)
                else:
                    return JsonResponse("Something went wrong!",safe=False,content_type='application/json; charset=utf8')
                
            if user_id:#delete unchecked menus for the selected user
                UserPermission.objects.filter(user_id = user_id).exclude(menu_id__in = menu_id_list).delete()
            return JsonResponse("User access control setup successful",safe=False,content_type='application/json; charset=utf8')
        else:        
            context = {
                'menu_list': MenuList.objects.filter(status = True).order_by('module_name','menu_order'),
                'designation_list': Designations.objects.all().order_by('name'),
                'department_list': Departments.objects.all().order_by('name'),
                'user_roles': UserRoles.objects.filter(status = True).order_by('name'),
                'user_list': Users.objects.filter(status = True),
                'company_list': Company.objects.all().order_by('name'),
            }
            return render(request, 'user/user_access_control_setup.html',context)
    else:
        return redirect('/access-denied')

@csrf_exempt
@login
def load_user_access_list(request):
    chk_permission   = permission(request, reverse("user_access_control_setup"))
    if chk_permission and chk_permission.view_action:
        if ebs_bl_common.is_ajax(request):
            access_list = list(UserPermission.objects.values().filter(user_id = int(request.POST.get('user'))))
            data = {
                "access_list":access_list,
            }
        return JsonResponse(data,safe=False,content_type='application/json; charset=utf8')
    else:
        return JsonResponse("You have no access on this action!",safe=False,content_type='application/json; charset=utf8')
                
@login
def user_access_control_list(request):
    chk_permission   = permission(request, reverse("user_access_control_list"))
    if chk_permission and chk_permission.view_action:
        user_roles = UserRoles.objects.filter(status = True).order_by('name')
        user_list  = Users.objects.filter(status = True)

        if request.method == 'POST':
            user_id   = request.POST.get('user')
            user_role = request.POST.get('user_role')
            access_list = []
            if user_id and not user_role:
                access_list = UserPermission.objects.filter(user_id = int(user_id)).order_by("menu__module_name")

            context = {
                'access_list': access_list,
                'user_roles': user_roles,
                'user_list': user_list,
                'user_id': int(user_id) if user_id else None,
            }
            return render(request, 'user/user_access_control_list.html', context)    
        else:        
            access_list = UserPermission.objects.filter(user_id = request.session.get('id')).order_by("menu__module_name")

            context = {
                    'access_list': access_list,
                    'user_roles': user_roles,
                    'user_list': user_list
                }
            return render(request, 'user/user_access_control_list.html', context)
    else:
        return redirect('/access-denied')
                
@csrf_exempt
@login
def delete_user_access_control(request, id):
    chk_permission   = permission(request, reverse("user_access_control_list"))
    if chk_permission and chk_permission.view_action and chk_permission.delete_action:
        UserPermission.objects.filter(id=id).delete()
        return JsonResponse("success",safe=False,content_type='application/json; charset=utf8')
    else:
        return JsonResponse("You have no access on this action!",safe=False,content_type='application/json; charset=utf8')
    
@login
def access_denied(request):
    return render(request, 'errors/403.html')


def page_not_found(request, exception=''):
    return render(request, 'errors/404.html')

@csrf_exempt
@login
def password_reset(request):
    chk_permission   = permission(request, reverse("user_index"))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(Users, id=request.POST.get('user_id'))
        if instance:
            md5_obj = hashlib.md5((instance.employee_id).encode())
            encripted_pass = md5_obj.hexdigest()
       
            instance.password = encripted_pass
            instance.password_text = instance.employee_id
            instance.save()
            data = {
                "status":'success',
                "msg":'Password Reset Successful.',
            }
            return JsonResponse(data, safe=False)
        else:
            data = {
                "status":'not_found',
                "msg":'User Not Found!',
            }
            return JsonResponse(data, safe=False)
    else:
        data = {
            "status":'no_permission',
            "msg":'You have no access on this action!',
        }
        return JsonResponse(data, safe=False)

def forgot_password(request):
    if request.method == 'POST':
        user_email = request.POST.get("user_email")
        if user_email:
            check_user = Users.objects.filter(email = user_email, status=True)
            if check_user:
                md5_obj = hashlib.md5(str(random.randint(0,999999)+31).encode())
                encripted_token = md5_obj.hexdigest()
                obj = ForgotPassword.objects.create(email = user_email, token=encripted_token)
                if obj:
                    msg = "<a href='/password/"+str(obj.token)+"/reset'>Please click this link to reset your password</a> <br><br>N.B. This is system generated email. Please do not reply."
                    mail = EmailMessage("HRM||Forgot Password", msg , settings.EMAIL_HOST_USER, [str(obj.email)])
                    mail.content_subtype = "html"
                    mail.send()
                    messages.info(request,"Password reset link has been sent to "+str(user_email)+". This link will valid for 30 minutes.")
                else:
                    messages.warning(request,"Something went wrong!")    
            else:
                messages.warning(request,"There is no user with "+str(user_email)+" email! Please input a valid email address.")    
        else:
            messages.warning(request,"Please Enter Your Email!")    
    return render(request, 'forgot_password.html')    

def forgot_password_reset(request,token):
    token_chk = ForgotPassword.objects.filter(token=token).first()
    if token_chk:
        if not token_chk.is_used:
            time_diff = str(datetime.now() - token_chk.created_at).split(":")
            if len(time_diff[0]) == 1 and int(time_diff[0]) < 1 and int(time_diff[1]) <= 30: # if day is not greater than 0 and hour less than 1 and min less than or equal 30 then the token is expired
                if request.method == "POST":
                    if request.POST.get("new_pass") == request.POST.get("confirm_pass"):
                        md5_obj = hashlib.md5(str(request.POST.get("new_pass")).encode())
                        encripted_token = md5_obj.hexdigest()
                        Users.objects.filter(email = token_chk.email).update(password = encripted_token, password_text=request.POST.get("new_pass"))
                        ForgotPassword.objects.filter(id = token_chk.id).update(is_used = True)
                        messages.success(request, "Password Reset Successful. You can login now.")
                        return redirect("/")
                    else:
                        messages.warning(request, "New password & confirm password doesn't matched!") 
                        return render(request, 'forgot_password_reset.html') 
                else:    
                    return render(request, 'forgot_password_reset.html')    
            else:   
                messages.warning(request,"This token has expired! Please try again with new token. Please try again.") 
                return redirect('/forgot-password')    
       
        else:
            messages.warning(request,"This token has already used! Please try again.")
            return redirect('/forgot-password') 
    else:
        messages.warning(request,"Invalid Token")
        return render(request, 'forgot_password.html')    
    return render(request, 'forgot_password_reset.html')    

@login
def bank_list(request):
    chk_permission = permission(request, reverse('bank_list'))
    if chk_permission and chk_permission.view_action:
        page_number = request.GET.get('page', 1)
        if request.method == 'POST':
            status = checkDuplicate(request, Bank)
            form = BankForm(request.POST)
            if status == 1:
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully added Bank")
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))

        template_name = 'bank_list.html'
        bank_list = Bank.objects.order_by('-id').all()
        action_name = 'Add Bank'
        action_url = reverse_lazy('bank_list')
        context = {
            'page_number':page_number,
            'template_name': template_name,
            'banks': bank_list,
            'action_url': action_url,
            'action_name': action_name,
        }
        return render(request, template_name, context )
    else: return redirect(reverse("access_denied"))

@login
def bank_update(request, id):
    try:
        page_number = request.GET.get('page',1)
        bank = get_object_or_404(Bank, id=id)
        if request.method == 'POST':
            status = checkDuplicate(request, Bank,id)
            form = BankForm(request.POST, instance=bank)
            if Bank.objects.exclude(id = bank.id).filter(name = form.data['name'], swift_code = form.data['swift_code']).exists():
                messages.success(request, 'Bank updated successfully')
            else:
                if form.is_valid():
                    form.save()
                    messages.success(request, 'successfully updated')
                    return redirect(request.META.get('HTTP_REFERER'))
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
        
        template_name = "bank_list.html"
        action_name = "Update Bank"
        action_url = reverse_lazy('bank_update', kwargs={'id': id})
        bank_list = Bank.objects.order_by('-id').all()
        context = {'banks': bank_list,'action_name' : action_name, 'action_url' : action_url, 'page_number' : page_number, 'bank' : bank }
        return render(request, template_name, context)
    except:
        return redirect(reverse_lazy('bank_list'))

def get_user_list(request):
    user = request.GET.get('q[term]', '')
    user_list = Users.objects.filter(Q(name__icontains=user)|Q(employee_id__icontains=user)).order_by('name').values('id', 'name', 'employee_id')
    new_list = []
    for user in user_list:
        new_list.append({'id': user['id'], 'text': user['name'] + " ( " + user['employee_id'] + " ) "})
    return JsonResponse({'users': new_list}, safe=False)

@login
@csrf_exempt
def get_user_department(request):
    user = request.GET.get('issued_to')
    user_department = Users.objects.get(id=int(user)).department.id
    return JsonResponse({'user_department': user_department})

@csrf_exempt
def get_department_wise_section(request):
    department_id = request.POST.get('department_id', '')
    section_list = Sections.objects.order_by('name').filter(department_id=department_id)
    new_list=[]
    new_list.append({'id': '', 'text': 'Section'})
    for section in section_list:
        new_list.append({'id': section.id, 'text': section.name })

    return JsonResponse({'sections': new_list}, safe=False)

# Custom template for not found page
@login
def error_404(request, *args, **argv):
    context = { "request":request }
    return render(request,'error_404.html', context)

# Custom template for not found page
def error_500(request, *args, **argv):
    import sys
    from django.views.debug import ExceptionReporter
    reporter = ExceptionReporter(request, *sys.exc_info())
    context = reporter.get_traceback_data()
    return render(request,'error_500.html', context)

def get_attendance(request):
    template_name   = "attendance.html"
    attendances     = []
    # with connections['mysql'].cursor() as cursor:
    #     cursor.execute("SELECT CONFID FROM sys_conf")
    #     rows = cursor.fetchall()
    #     for index, row in enumerate(rows):
    #         print(index, row)
    context         = {'attendances':attendances}
    return render(request, template_name, context)


# ============ Departments Start ============ #
try: 
    from general.view.departments import *
except Exception as e: 
    print('bjbjfbj:::', e)
    pass
# ============ Departments End ============ #

# ============ Designations Start ============ #
try: 
    from general.view.designations import *
except ImportError: pass
# ============ Designations End ============ #

# ============ Sections Start ============ #
try: from general.view.sections import *
except ImportError: pass
# ============ Sections End ============ #

