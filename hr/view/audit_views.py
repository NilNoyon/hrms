from datetime import date, datetime, timedelta, timezone
import os
import time
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, reverse, render
from general.decorators import login, permission
from general.models import Company
from django.db.models import Q
from django.contrib import messages
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.files.storage import FileSystemStorage 
from django.core.files.base import ContentFile
from general.models import CommonMaster
from hr.forms import AuditStatusForm

from hr.models import AuditStatus



@login
def audit_status_entry(request):
    chk_permission   = permission(request, reverse('hr:audit_status_entry'))
    if chk_permission and chk_permission.insert_action:
        if request.method == 'POST':
            request.POST = request.POST.copy()
            request.POST['last_audit_date'] = datetime.strptime(request.POST.get('last_audit_date'), "%d-%b-%Y").date() if request.POST.get('last_audit_date') else ''
            request.POST['expire_date'] = datetime.strptime(request.POST.get('expire_date'), "%d-%b-%Y").date() if request.POST.get('expire_date') else ''
            attachment = ""
            if bool(request.FILES.get('attachment', False)) == True:
                attachment = request.FILES['attachment']
                if not os.path.exists(str(settings.MEDIA_ROOT) + '/attachment/'):
                    os.mkdir(str(settings.MEDIA_ROOT) + '/attachment/')
                    file_extnsn = str(str(attachment).split(".")[1].lower())
                    default_storage.save(str(settings.MEDIA_ROOT) + "/attachment/" + str("Audit_attachment") + "." + file_extnsn,
                    ContentFile(attachment.read()))
                    attachment = "/attachment/" + str("Attachment") + "." + file_extnsn
            form = AuditStatusForm(request.POST,request.FILES)
            if form.is_valid():
                obj = form.save()
                obj.save()
                message = 'Audit Status Entry Successful!'
                messages.success(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error)) 
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                   audit_status_list = AuditStatus.objects.all()
            else:
                audit_status_list = AuditStatus.objects.filter(Q(company = request.session.get('company'))|
                                    Q(company = request.session.get('company_short_name'))).exclude(employee_id = 'admin')
            company_list = Company.objects.filter(status=True)
            action = {'name': 'Add New', 'btnTxt': 'Submit'}
            context = {
                'audit_status_list' : audit_status_list,
                'action': action,
                'company_list': company_list,
            }
        return render(request, 'audit_status/audit_status_entry.html', context)
    else:
        return redirect('/access-denied')



@login
def audit_status_update(request, id):
    chk_permission   = permission(request,reverse('hr:audit_status_entry'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(AuditStatus, id=id)
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                request.POST['last_audit_date'] = datetime.strptime(request.POST.get('last_audit_date'), "%d-%b-%Y").date() if request.POST.get('last_audit_date') else ''
                request.POST['expire_date'] = datetime.strptime(request.POST.get('expire_date'), "%d-%b-%Y").date() if request.POST.get('expire_date') else ''
                form = AuditStatusForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    message = ' License Info Successfully Updated'
                    messages.success(request, message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                else:
                    for field in form:
                        for error in field.errors:
                            messages.warning(request, "%s : %s" % (field.name, error))
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                    audit_status_list = AuditStatus.objects.all()
                else:
                    audit_status_list = AuditStatus.objects.filter(Q(company = request.session.get('company'))|
                                        Q(company = request.session.get('company_short_name'))).exclude(employee_id = 'admin')
                company_list = Company.objects.filter(status=True)
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    'instance': instance, 
                    'action': action, 
                    'audit_status_list': audit_status_list,
                    'company_list': company_list,
                    'option':'option',
                }
                return render(request, 'audit_status/audit_status_entry.html', context)
        else:   
            messages.warning(request,"Audit Status details not found!")
            return redirect('hr:audit_status_entry')        
    else:
        return redirect('/access-denied')


@login
def audit_status_view(request, id):
    instance = get_object_or_404(AuditStatus, id=id)
    if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
        audit_status_list = AuditStatus.objects.all()
    else:
        audit_status_list = AuditStatus.objects.filter(Q(company = request.session.get('company'))|
                            Q(company = request.session.get('company_short_name'))).exclude(employee_id = 'admin')
    action = {'name': 'Add New', 'btnTxt': 'Submit'}
    context = {
        'instance': instance, 
        'action': action, 
        'audit_status_list': audit_status_list,
    }
    return render(request, 'audit_status/audit_status_view.html', context)