from datetime import date, datetime, timedelta, timezone
import os, time
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect,reverse, render
from general.decorators import login, permission
from general.models import CommonMaster, Company, Branch
from hr.forms import License
from hr.models import LicenseInfo
from django.db.models import Q
from django.contrib import messages
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.files.storage import FileSystemStorage 
from django.core.files.base import ContentFile
from dateutil import relativedelta


@login
def licinse_entry(request):
    chk_permission   = permission(request, reverse('hr:licinse_entry'))
    if chk_permission and chk_permission.insert_action:
        if request.method == 'POST':
            request.POST = request.POST.copy()
            request.POST['issu_date'] = datetime.strptime(request.POST.get('issu_date'), "%d-%b-%Y").date() if request.POST.get('issu_date') else ''
            request.POST['expire_date'] = datetime.strptime(request.POST.get('expire_date'), "%d-%b-%Y").date() if request.POST.get('expire_date') else ''
            request.POST['branch'] = request.POST.get('company')
            attachment = ""
            if bool(request.FILES.get('attachment', False)) == True:
                attachment = request.FILES['attachment']
                if not os.path.exists(str(settings.MEDIA_ROOT) + '/attachment/'):
                    os.mkdir(str(settings.MEDIA_ROOT) + '/attachment/')
                    file_extnsn = str(str(attachment).split(".")[1].lower())
                    default_storage.save(str(settings.MEDIA_ROOT) + "/attachment/" + str("Attachment") + "." + file_extnsn,
                    ContentFile(attachment.read()))
                    attachment = "/attachment/" + str("Attachment") + "." + file_extnsn
            form = License(request.POST,request.FILES)
            if form.is_valid():
                obj = form.save()
                obj.save()
                message = 'License Entry Successful!'
                messages.success(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error)) 
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            license_list = []
            if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                license_list=LicenseInfo.objects.all()
            else:
                license_list=LicenseInfo.objects.filter(Q(company = request.session.get('company'))| Q(company = request.session.get('company_short_name'))).exclude(employee_id = 'admin')
            
            license_data_list=[] 
            for data in license_list: 
                expire_date = data.expire_date
                to_date = datetime.now().date()
                date1 = datetime(expire_date.year, expire_date.month, expire_date.day)
                date2 = datetime(to_date.year, to_date.month, to_date.day)
                diff = relativedelta.relativedelta(date1, date2)
                year = abs(int(diff.years)) 
                month = abs(int(diff.months))
                day = abs(int(diff.days))
                if year == 0 and not month == 0:
                    tenure = str(month) + " month "+str(day)+" days"
                elif month != 0:
                    tenure = str(month) + " month "+str(day)+" days"
                elif year == 0 and month == 0:
                    tenure = str(day)+" days"
                else:
                    tenure =  str(year)+ " years "+str(month) + " month "+str(day)+" days"
                
                obj={
                    'id':data.id,
                    'company':data.branch,
                    'license_name': data.license_name,
                    'certificate_no' : data.certificate_no,
                    'issu_date' : data.issu_date,
                    'expire_date' : data.expire_date,
                    'renewal_status' : data.renewal_status,
                    'remarks' : data.remarks,
                    'tenure' : tenure
                }
                license_data_list.append(obj) 

            license_name = CommonMaster.objects.filter(value_for = "12")
            company_list = Branch.objects.filter(status=True,company_id=request.session.get('company_id'))
            action = {'name': 'Add New', 'btnTxt': 'Submit'}
            context = {
                'license_data_list' : license_data_list,
                'action': action, 
                'company_list': company_list,
                'license_name':license_name,
            }
        return render(request, 'license/license.html', context)
    # else:
    #     return redirect('/access-denied')

@login
def license_entry_update(request, id):
    chk_permission   = permission(request, reverse('hr:licinse_entry'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        instance = get_object_or_404(LicenseInfo, id=id)
        if instance:
            if request.method == 'POST':
                request.POST = request.POST.copy()
                request.POST['issu_date'] = datetime.strptime(request.POST.get('issu_date'), "%d-%b-%Y").date() if request.POST.get('issu_date') else ''
                request.POST['expire_date'] = datetime.strptime(request.POST.get('expire_date'), "%d-%b-%Y").date() if request.POST.get('expire_date') else ''
                request.POST['branch'] = request.POST.get('company')
                form = License(request.POST, instance=instance)
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
                license_list = []
                if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
                    license_list=LicenseInfo.objects.all()
                else:
                    license_list=LicenseInfo.objects.filter(Q(company = request.session.get('company'))| Q(company = request.session.get('company_short_name'))).exclude(employee_id = 'admin')
                
                license_data_list=[] 
                for data in license_list: 
                    expire_date = data.expire_date
                    to_date = datetime.now().date()
                    date1 = datetime(expire_date.year, expire_date.month, expire_date.day)
                    date2 = datetime(to_date.year, to_date.month, to_date.day)
                    diff = relativedelta.relativedelta(date1, date2)
                    year = abs(int(diff.years)) 
                    month = abs(int(diff.months))
                    day = abs(int(diff.days))
                    if year == 0 and not month == 0:
                        tenure = str(month) + " month "+str(day)+" days"
                    elif month != 0:
                        tenure = str(month) + " month "+str(day)+" days"
                    elif year == 0 and month == 0:
                        tenure = str(day)+" days"
                    else:
                        tenure =  str(year)+ " years "+str(month) + " month "+str(day)+" days"
                    
                    obj={
                        'id':data.id,
                        'company':data.branch,
                        'license_name': data.license_name,
                        'certificate_no' : data.certificate_no,
                        'issu_date' : data.issu_date,
                        'expire_date' : data.expire_date,
                        'renewal_status' : data.renewal_status,
                        'remarks' : data.remarks,
                        'tenure' : tenure
                    }
                    license_data_list.append(obj) 
                    license_name = CommonMaster.objects.filter(value_for = "12")
                    company_list = Branch.objects.filter(status=True,company_id=request.session.get('company_id'))
                    action = {'name': 'Update', 'btnTxt': 'Update'}
                    context = {
                        'instance': instance, 
                        'action': action, 
                        'license_data_list': license_data_list,
                        'company_list': company_list,
                        'license_name':license_name,
                        'option':'option',
                    }
                return render(request, 'license/license.html', context)
        else:   
            messages.warning(request,"License details not found!")
            return redirect('hr:licinse_entry')        
    # else:
    #     return redirect('/access-denied')

@login
def license_view(request, id):
    instance = get_object_or_404(LicenseInfo, id=id)
    if request.session["role_text"].lower() in ["admin", "super admin","user"]: 
        license_list = LicenseInfo.objects.all()
    else:
        license_list = LicenseInfo.objects.filter(Q(company = request.session.get('company'))|
                            Q(company = request.session.get('company_short_name'))).exclude(employee_id = 'admin')
    action = {'name': 'Add New', 'btnTxt': 'Submit'}
    context = {
        'instance': instance, 
        'action': action, 
        'license_list': license_list,
    }
    return render(request, 'license/license_view.html', context)

