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
# from hr.models import EmployeeInfo, EmployeeDetails
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
                         request.session['hd_role']              = str(user[0].helpdesk_role)
                         request.session['company']              = str(user[0].company.name)
                         request.session['company_id']           = str(user[0].company_id)
                         request.session['company_id_list']      = request.session['secondary_company'] + [user[0].company_id]
                         request.session['department']           = str(user[0].department.name)
                         request.session['company_short_name']   = str(user[0].company.short_name)
                    except Exception as e:
                         messages.warning(request, str(e))
                         return render(request, "login.html",{"employee_id":request.POST['employee_id']})
                    # try:
                    #      employee_info = EmployeeInfo.objects.get(employee_id=user[0].employee_id)
                    #      request.session['photo']        = str(employee_info.photo) if employee_info.photo else ''
                    #      request.session['emp_email']    = str(employee_info.email) if employee_info.email else False
                    #      request.session['emp_phone']    = str(employee_info.phone_no) if employee_info.phone_no else False
                    # except EmployeeInfo.DoesNotExist : request.session['photo'] = ''
                    
                    messages.success(request, "Login Successful.")
                    next_url = request.POST.get("next_url")
                    return redirect("dashboard") if not next_url else redirect(next_url)
               else:
                    messages.warning(request, "Invalid password!")
                    return render(request, "login.html",{"employee_id":request.POST['employee_id']})
          else:
               messages.warning(request, "Invalid employee ID!")
               return render(request, "login.html",{"employee_id":request.POST['employee_id']})

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
     try:
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
               'hide_bulleting_data':hide_bulleting_data,
               # 'operation_bulletin_ekcl': operation_bulletin_ekcl
          }
          return render(request, 'home1.html', context )
     except Exception as e:
          messages.warning(request,str(e))
          return render(request, 'home2.html' )