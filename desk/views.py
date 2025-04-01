from django.contrib.sessions.models import Session
from notification.models import Notification
import django
from django.shortcuts import render, redirect, get_object_or_404, reverse, resolve_url
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from desk.models import Issue, AssessmentDeviceList, DeviceAssessments
from .forms import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Q
import ast, json, os, random
from datetime import datetime, date, timedelta
from django.utils.dateformat import DateFormat
from hr.models import EmployeeDetails
from general.views import syncUsers #used for synchronus user with employee
from general.decorators import login, permission
from PIL import Image
from general.utils import render_to_pdf
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pandas as pd
from notification.signals import notify
from django.urls import reverse
from general.models import CommonMaster

@login
def issue_dashboard(request):
         
    method_chk = "get"
    if request.method == 'POST':
        now = datetime.now()
        # date = (DateFormat(now)).format('Y/m/d')
        day = (DateFormat(now)).format('d')
        month = (DateFormat(now)).format('m')
        year = (DateFormat(now)).format('Y')
        year2 = (DateFormat(now)).format('y')

        files = request.FILES.getlist('attachment')
        fabric_order       = request.POST.get("fo",None) or None
        taged_to           = request.POST.get("taged_user",None) or None
        count = format(Issue.objects.filter(created_at__gte=date.today()).count() + 1, '04d')
        ref = str(year2)+str(month)+str(day)+count

        attachment = ""
        i = 1
        try:
            for myfile in files:
                if myfile.size < settings.DATA_UPLOAD_LIMIT: 
                    ext = os.path.splitext(myfile.name)[-1].lower()
                    fs = FileSystemStorage()
                    filename = "supportdesk/"+year+'/'+month+'/'+day +'/'+ref+'-'+str(i)+ext
                    fs.save(filename, myfile)
                    attachment += filename
                    if i != len(files): attachment+= ","
                    i = i+1
        except: pass

        if len(request.POST['description']) > 0:
            issue_obj = Issue.objects.create(fabric_order_no = fabric_order,taged_to_id = taged_to, ref = ref, issuer_id = request.session.get("id"), description = request.POST['description'], attachment = attachment)
            method_chk = "post"
            messages.success(request,"Issue has been raised.")
            if issue_obj: 
                n_recipient = Users.objects.filter(id = taged_to)
                # Send Notification
                if n_recipient:
                    n_model = 'Issue'
                    n_verb = 'You have A Complain'
                    n_description = issue_obj.issuer.name+" sent you a complain. Please Check on supportdesk Complain No: #"+issue_obj.ref
                    n_is_repeated = False
                    n_sender = Users.objects.get(id=request.session.get("id"))
                    n_action_url = reverse('desk:issue_dashboard')
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)

        else:
            messages.warning(request, "Please fill up the fields!")
    
    pending_issue_list, my_issue_list, assigned_issue_list, solved_issue_list,textile_issue_list = [], [], [], [],[]
    if int(request.session.get("hd_role")) in [2, 3, 4]: #if the user is manager or department head
        pending_issue_list = Issue.objects.filter(status = "1").order_by('-created_at','-id')
        my_issue_list = Issue.objects.filter((Q(status = "2")|Q(status = "3")|Q(status = "4")), assigned_to = int(request.session.get("id"))).order_by('status','-id')
        assigned_issue_list = Issue.objects.filter(Q(status = "2")|Q(status = "3")).exclude(assigned_to = int(request.session.get("id"))).order_by('-assigned_at','-id')
        solved_issue_list = Issue.objects.filter(status = "4").exclude(assigned_to = int(request.session.get("id"))).order_by('-resolved_at','-id')
        textile_issue_list = Issue.objects.filter(fabric_order_no__isnull = False).exclude(assigned_to = int(request.session.get("id"))).order_by('-resolved_at','-id')
        # solved_issue_list = Issue.objects.filter(status = "4").order_by('-resolved_at','-id')
        # resolver_list = Users.objects.filter(Q(supportdesk_role = 2)|Q(supportdesk_role = 3))
        # context = {'issues': issues, 'resolver_list':resolver_list,'method_chk':method_chk}
        # return render(request, 'issue/issue_entry.html', context)
    # elif int(request.session.get("hd_role")) == 1: #this is for resolver dashboard filtering
    #     pending_issue_list = Issue.objects.filter(status = "1").order_by('-id')
    #     issues = Issue.objects.filter((Q(status = "2")|Q(status = "3")), assigned_to = int(request.session.get("id"))).order_by('-id')
    #     context = {'issues': issues,'method_chk':method_chk}
    #     return render(request, 'issue/issue_entry.html', context)
    else:
        my_issue_list = Issue.objects.filter(Q(issuer_id = int(request.session.get("id")))| Q(taged_to_id = int(request.session.get("id")))).order_by('status','-id')
    
    taged_user = Users.objects.filter(status= True)

    context = {
        "pending_issue_list":pending_issue_list,
        "my_issue_list":my_issue_list,
        "assigned_issue_list":assigned_issue_list,
        "solved_issue_list":solved_issue_list,
        "textile_issue_list":textile_issue_list,
        "method_chk":method_chk,
        "taged_user":taged_user,
    }
    return render(request, 'issue/issue_entry.html', context)

# Business Logic
from general.business_logic import common_logic
ebs_bl_common = common_logic.Common()

@csrf_exempt
def get_issues_for_dataTable(request):
    data_list = []
    search_text = request.POST.get('search[value]', '')
    start = int(request.POST.get('start', 0))
    issue_list = Issue.objects.filter(status = '4').order_by("-id")
    
    if search_text:
        issue_list = issue_list.filter(
                        Q(ref__icontains=search_text) 
                        | Q(issuer__employee_id__icontains=search_text)
                        | Q(issuer__name__icontains=search_text)
                        | Q(description__icontains=search_text)
                        | Q(resolver_note__icontains=search_text)
                        | Q(resolved_at__icontains=search_text)
                        | Q(created_at__icontains=search_text)
                    )

    issue_list = issue_list[start:start+20]

    for issue in issue_list:
        attachment, expand_desc, resolver_note, expand_note = "", "", "", ""
        if len(issue.description.split(" ")) > 10:
            expand_desc += """<i class="fas fa-arrow-circle-down" onclick="expand_td('issue_desc_"""+str(issue.id)+"""');" style="color:blue;"></i>"""
        
        if issue.resolver_note and len(issue.resolver_note.split(" ")) > 8:
            expand_note += """<i class="fas fa-arrow-circle-down" onclick="expand_td('feedback_"""+str(issue.id)+"""');" style="color:blue;"></i>"""
        
        if issue.attachment: 
            for a in str(issue.attachment).split(","):
               attachment += '<a href="/assets/uploads/'+str(a)+'" target="_blank"><i class="icon-link"></i> </a>'  
      
        description = """
            <span class="issue_desc_"""+str(issue.id)+"""_show">"""+str(issue.description[0:30] if issue.description else "N/A")+attachment+expand_desc+""" </span>
            <span class="issue_desc_"""+str(issue.id)+"""_hide" style="display:none">"""+str(issue.description)+attachment+""" <i class='fas fa-arrow-circle-up' onclick="close_td('issue_desc_"""+str(issue.id)+"""');" style="color:blue;"></i></span>

        """
        resolver_note = """
            <span class="feedback_"""+str(issue.id)+"""_show">"""+str(issue.resolver_note[0:20] if issue.resolver_note else "N/A")+expand_note+""" </span>
            <span class="feedback_"""+str(issue.id)+"""_hide" style="display:none">"""+str(issue.resolver_note)+""" <i class='fas fa-arrow-circle-up' onclick="close_td('feedback_"""+str(issue.id)+"""');" style="color:blue;"></i></span>

        """
        issuer      = ebs_bl_common.user_html(issue.issuer, 15)
        resolver    = ebs_bl_common.user_html(issue.assigned_by_name(), 15)
        data = [issue.ref, description, issuer, issue.created_at.strftime("%d-%b-%Y %I:%M %p").upper(), issue.resolved_at.strftime("%d-%b-%Y %I:%M %p").upper(), resolver_note, resolver]
        data_list.append(data)

    return JsonResponse(data_list, safe=False)

@login
def issue_dashboard_old(request):
         
    method_chk = "get"
    if request.method == 'POST':
        now = datetime.now()
        # date = (DateFormat(now)).format('Y/m/d')
        day = (DateFormat(now)).format('d')
        month = (DateFormat(now)).format('m')
        year = (DateFormat(now)).format('Y')
        year2 = (DateFormat(now)).format('y')

        files = request.FILES.getlist('attachment')
        count = format(Issue.objects.filter(created_at__gte=date.today()).count() + 1, '04d')
        ref = str(year2)+str(month)+str(day)+count

        attachment = ""
        i = 1
        for myfile in files:
            ext = os.path.splitext(myfile.name)[-1].lower()
            fs = FileSystemStorage()
            filename = "supportdesk/"+year+'/'+month+'/'+day +'/'+ref+'-'+str(i)+ext
            fs.save(filename, myfile)
            attachment += filename
            if i != len(files): attachment+= ","
            i = i+1

        if len(request.POST['description']) > 0:
            issue_obj = Issue.objects.create(ref = ref, issuer_id = request.session.get("id"), description = request.POST['description'], attachment = attachment)
            method_chk = "post"
            
            if issue_obj:
                hd_manager = Users.objects.filter(supportdesk_role = "3").first()
                
                if hd_manager:
                    # Send Notification
                    n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                    n_recipient     = get_object_or_404(Users,id = hd_manager.id)
                    n_action_url    = reverse('desk:issue_dashboard')
                    n_model         = 'Issue'
                    n_verb          = 'supportdesk New Issue'
                    n_description   = "1 new issue(" + issue_obj.ref + ") raised in supportdesk"
                    n_is_repeated   = False
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                
                ict_dpt_head = Users.objects.filter(designation__name = "Head of ICT", is_department_head = True).first()
                if ict_dpt_head and ict_dpt_head.email: 
                    # Send Notification
                    n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                    n_recipient     = get_object_or_404(Users,id = ict_dpt_head.id)
                    n_action_url    = reverse('desk:issue_dashboard')
                    n_model         = 'Issue'
                    n_verb          = 'supportdesk Issue'
                    n_description   = "1 new issue raised in supportdesk"
                    n_is_repeated   = True
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                    
                    subject = "EBS #" + issue_obj.ref + " - Issue Raised on Supportdesk"
                    msg = "Issue has been raised <a href=/supportdesk/"+">"+"#" + issue_obj.ref +"</a> <br>Description: " + issue_obj.description+"<br><br>Issuer Name: "+str(issue_obj.issuer)+"<br>Issuer Email: "+str(issue_obj.issuer.email)+"<br>Issuer ID: "+str(issue_obj.issuer.employee_id)+"<br>Issuer Department: "+str(issue_obj.issuer.department)+"  <br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                    mail = EmailMessage(subject, msg, settings.EMAIL_HOST_USER, [ict_dpt_head.email])
                    mail.content_subtype = "html"
                    mail.send()
                    messages.success(request,"Issue has been raised.")  
            
        else:
            messages.warning(request, "Please fill up the fields!")

    if int(request.session.get("hd_role")) == 4 or int(request.session.get("hd_role")) == 3: #if the user is manager or department head
        issues = Issue.objects.filter(Q(status = "1")).order_by('-id')
        resolver_list = Users.objects.filter(Q(supportdesk_role = 2)|Q(supportdesk_role = 3))
        context = {'issues': issues, 'resolver_list':resolver_list,'method_chk':method_chk}
        return render(request, 'issue/issue_entry.html', context)
    elif int(request.session.get("hd_role")) == 2: #this is for resolver dashboard filtering
        issues = Issue.objects.filter((Q(status = "2")|Q(status = "3")), assigned_to = int(request.session.get("id"))).order_by('-id')
        context = {'issues': issues,'method_chk':method_chk}
        return render(request, 'issue/issue_entry.html', context)
    else:
        issues = Issue.objects.filter(Q(issuer_id = int(request.session.get("id")))|Q(assigned_by = int(request.session.get("id")))|Q(assigned_to = int(request.session.get("id")))).order_by('-id')
        context = {'issues': issues,'method_chk':method_chk}
        return render(request, 'issue/issue_entry.html', context)

@login
def search_issue(request):
    if int(request.session.get("hd_role")) == 4 or int(request.session.get("hd_role")) == 3 or int(request.session.get("hd_role")) == 2:
        if request.method == 'POST':
            if "issue_type" in request.POST:
                issue_type = request.POST.get('issue_type')
                if issue_type == "1":
                    issues = Issue.objects.filter(status = "1").order_by('-id')
                elif issue_type == "2":
                    issues = Issue.objects.exclude(status = "1").order_by('status','-id')
                else:
                    issues = Issue.objects.filter(Q(issuer_id = int(request.session.get("id")))|Q(assigned_by = int(request.session.get("id")))|Q(assigned_to = int(request.session.get("id")))).order_by('status','-id')

                resolver_list = Users.objects.filter(supportdesk_role = 2)
                context = {'issues': issues, 'issue_type':issue_type, 'resolver_list':resolver_list}
                return render(request, 'issue/issue_entry.html', context)
            elif "resolver_issue_type" in request.POST:
                resolver_issue_type = str(request.POST.get('resolver_issue_type'))
                issues = Issue.objects.filter(assigned_to = int(request.session.get("id")), status = resolver_issue_type).order_by('-id')
                context = {'issues': issues, 'resolver_issue_type':resolver_issue_type}
                return render(request, 'issue/issue_entry.html', context)
        else:   
            return redirect('/supportdesk/')
    else:
        messages.warning(request, "You have no access for this action!")    
        return redirect('/supportdesk/')

@login
def supportdesk_report(request):
    if int(request.session.get("hd_role")) == 4 or request.session["role_text"] == "Admin" or request.session["role_text"] == "Super Admin":
        resolver_list = Users.objects.filter(Q(supportdesk_role = 2)|Q(supportdesk_role = 3)).order_by('name')
        if request.method == 'POST':
            issue_type  = request.POST.get('issue_type')
            resolver    = request.POST.get('resolver')
            issueDateRange = request.POST.get('issueDateRange')
            issues = []
            if issue_type and not resolver and not issueDateRange:
                if issue_type == "2":
                    issues = Issue.objects.filter(Q(status = "2")|Q(status = "3")|Q(status = "4")).order_by('status','-id')
                else:    
                    issues = Issue.objects.filter(status = issue_type).order_by('-id')
            elif not issue_type and resolver and not issueDateRange:
                issues = Issue.objects.filter(assigned_to = resolver).order_by('-id')
            elif issue_type and resolver and not issueDateRange:
                if issue_type == "2":
                    issues = Issue.objects.filter(Q(status = "2")|Q(status = "3")|Q(status = "4"), assigned_to = resolver).order_by('status','-id')
                else:
                    issues = Issue.objects.filter(status = issue_type, assigned_to = resolver).order_by('status','-id')
            elif not issue_type and not resolver and issueDateRange:
                from_date = datetime.strptime(str(issueDateRange.split("-")[0].strip()), '%m/%d/%Y')
                to_date   = datetime.strptime(str(issueDateRange.split("-")[1].strip()), '%m/%d/%Y') + timedelta(1)
                issues = Issue.objects.filter(created_at__gte = from_date, created_at__lte = to_date).order_by('status','-id')
            elif issue_type and not resolver and issueDateRange:
                from_date = datetime.strptime(str(issueDateRange.split("-")[0].strip()), '%m/%d/%Y')
                to_date   = datetime.strptime(str(issueDateRange.split("-")[1].strip()), '%m/%d/%Y') + timedelta(1)
                if issue_type == "2":
                    issues = Issue.objects.filter(Q(status = "2")|Q(status = "3")|Q(status = "4"), created_at__gte = from_date, created_at__lte = to_date).order_by('status','-id')
                else:
                    issues = Issue.objects.filter(status = issue_type, created_at__gte = from_date, created_at__lte = to_date).order_by('status','-id')
            elif not issue_type and resolver and issueDateRange:
                from_date = datetime.strptime(str(issueDateRange.split("-")[0].strip()), '%m/%d/%Y')
                to_date   = datetime.strptime(str(issueDateRange.split("-")[1].strip()), '%m/%d/%Y') + timedelta(1)
                issues = Issue.objects.filter(assigned_to = resolver, created_at__gte = from_date, created_at__lte = to_date).order_by('status','-id')
            elif issue_type and resolver and issueDateRange:
                from_date = datetime.strptime(str(issueDateRange.split("-")[0].strip()), '%m/%d/%Y')
                to_date   = datetime.strptime(str(issueDateRange.split("-")[1].strip()), '%m/%d/%Y') + timedelta(1)
                if issue_type == "2":
                    issues = Issue.objects.filter(Q(status = "2")|Q(status = "3")|Q(status = "4"), assigned_to = resolver, created_at__gte = from_date, created_at__lte = to_date).order_by('status','-id')
                else:
                    issues = Issue.objects.filter(status = issue_type, assigned_to = resolver, created_at__gte = from_date, created_at__lte = to_date).order_by('status','-id')

            context = {
                'issueDateRange': issueDateRange,
                'issues': issues,
                'resolver':int(resolver) if resolver else None,
                'issue_type':issue_type,
                'resolver_list':resolver_list,
                }
            return render(request, 'issue/supportdesk_report.html', context)
        
        context = {'resolver_list':resolver_list}
        return render(request, 'issue/supportdesk_report.html', context)
        
    else:
        messages.warning(request, "You have no access for this page!")    
        return redirect('/supportdesk/')

@login
def phonebook(request):
    phonebook_list = EmployeeDetails.objects.filter(status = Status.name('active')
        ).exclude(Q(personal__employee_id='admin')|Q(employee_category__value__iexact='Worker')).order_by(
        'branch__short_name', 'department__name', 'personal__first_name')
    context = {'phonebook_list': phonebook_list}
    return render(request, 'phonebook.html', context)

@csrf_exempt
@login
def issue_assign(request):
    if request.method == 'POST':
        if 'assigned_to' and 'issue' in request.POST:
            issue = get_object_or_404(Issue, id=int(request.POST['issue']))
            issue.assigned_at = datetime.now()
            issue.assigned_by = int(request.session.get("id"))
            issue.assigned_to = int(request.POST['assigned_to'])
            issue.assign_note = request.POST['assign_note']
            issue.status = "2"
            issue.save()
            try:
                if len(str(request.POST['assign_note'])) > 0: assign_note = "<br>Assign Note: "+ request.POST['assign_note']
                else: assign_note = ""
                subject = "EBS #" + issue.ref + " - Issue assigned to you!"
                msg = "You have been assigned for this issue.<br>" + issue.description+"<br> Here is your assigned issue <a href=/supportdesk/"+">"+"#" + issue.ref +"</a>"+assign_note+"<br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                # Send Notification
                n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                n_recipient     = get_object_or_404(Users,id = int(request.POST['assigned_to']))
                n_action_url    = reverse('desk:issue_dashboard')
                n_model         = 'Issue'
                n_verb          = 'supportdesk Issue'
                n_description   = "1 new issue(" + issue.ref + ") assigned to you in supportdesk"
                n_is_repeated   = False
                notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                mail = EmailMessage(subject, msg, settings.EMAIL_HOST_USER, [issue.assigned_to_name().email])
                mail.content_subtype = "html"
                mail.send()
            except Exception as msg:
                return JsonResponse(str(msg), safe=False)

            message = 'Issue has been assigned to '+issue.assigned_to_name().name
            return JsonResponse(message, safe=False)
        else:
            return JsonResponse("Invalid Data", safe=False)
    return JsonResponse("Something went wrong!", safe=False)

@csrf_exempt
@login
def issue_cancel(request):
    if request.method == 'POST':
        issue = get_object_or_404(Issue, id=int(request.POST['issue']))
        issue.canceled_at = datetime.now()
        issue.canceled_by = int(request.session.get("id"))
        issue.canceled_note = request.POST['canceled_note']
        issue.status = "1" #Cancel means it will go again pending list
        issue.save()
        try:
            if len(str(request.POST['canceled_note'])) > 0: canceled_note = "<br>Cancel Note: "+ request.POST['canceled_note']
            else: canceled_note = ""
            subject = "EBS #" + issue.ref + " - Issue Canceled!"
            msg = "Your issue has canceled.<br>" + issue.description+"<br> Here is your canceled issue <a href=https://#/supportdesk/"+">"+"#" + issue.ref +"</a>"+canceled_note+"<br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
            # Send Notification
            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
            n_recipient     = get_object_or_404(Users,id = issue.issuer_id)
            n_action_url    = reverse('desk:issue_dashboard')
            n_model         = 'Issue'
            n_verb          = 'supportdesk Issue'
            n_description   = "Your issue("+ issue.ref +") is canceled in supportdesk"
            n_is_repeated   = False
            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
            
            # mail = EmailMessage(subject, msg, settings.EMAIL_HOST_USER, [issue.issuer.email])
            # mail.content_subtype = "html"
            # mail.send()
        except Exception as msg:
            return JsonResponse(str(msg), safe=False)

        message = 'Issue has been canceled.'
        return JsonResponse(message, safe=False)
    return JsonResponse("Something went wrong!", safe=False)

@csrf_exempt
@login
def issue_resolve(request):
    if request.method == 'POST':
        if 'status' and 'issue' in request.POST:
            resolve_note = request.POST.get('note')
            issue = get_object_or_404(Issue, id=int(request.POST['issue']))
            if issue.status in ["1", "2"] and request.POST['status'] == "2" or request.POST['status'] == "3":
                if issue.status == "1":
                    issue.assigned_at = datetime.now()
                    issue.assigned_by = int(request.session.get("id")) #self assign
                    issue.assigned_to = int(request.session.get("id"))
                issue.status = "3"

            elif request.POST['status'] == "4":
                if len(resolve_note) > 0: issue.resolver_note = resolve_note
                issue.resolved_at = datetime.now()
                issue.status = "4"
            issue.save()  
            message = ""    
            if issue.status == "3" and issue.assigned_to == int(request.session.get("id")):
                message = '#' + issue.ref + ' - Issue has been started!'
            elif issue.status == "4" and issue.assigned_to == int(request.session.get("id")):
                if len(resolve_note) > 0:msg = 'EBS #' + issue.ref + "- Issue has been solved by "+str(issue.assigned_to_name())+"<br><br>You have a note by "+str(issue.assigned_to_name())+" on your raised issue. Note: "+resolve_note+"<br> Here is your raised issue <a href=https://#/supportdesk/"+">"+"#" + issue.ref +"</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                else: msg = 'EBS #' + issue.ref + "- Issue has been solved by "+str(issue.assigned_to_name())+".<br>Here is your raised issue <a href=https://#/supportdesk/"+">"+"#" + issue.ref +"</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                subject = issue.ref + " - Issue Solved!"
                # Send Notification
                n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                n_recipient     = get_object_or_404(Users,id = issue.issuer_id)
                n_action_url    = reverse('desk:issue_dashboard')
                n_model         = 'Issue'
                n_verb          = issue.ref + " - Issue Solved!"
                n_description   = '#' + issue.ref + ' - Issue has been solved!'
                n_is_repeated   = True
                notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                
                if issue.issuer.email:
                    try:
                        issuer_mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, [str(issue.issuer.email)])
                        issuer_mail.content_subtype = "html"
                        issuer_mail.send()
                    except Exception as msg:
                        return JsonResponse(str(msg), safe=False)
                message = '#' + issue.ref + ' - Issue has been solved!'
            else:
                message = '#' + issue.ref + ' has already '+str(issue.status)+' to '+str(issue.assigned_to_name())
                # mail to issuer department head
                # if issue.issuer.reporting_to and issue.issuer.reporting_to.email:
                #     try:
                #         subject = 'EBS #' + issue.ref + " - Issue Solved!"
                #         msg = str(issue.issuer)+"'s issue has been solved by "+str(issue.assigned_to_name())+"<br> Issue detail: "+issue.description+"<br>Note: "+resolve_note+"<br> Here is the solved issue <a href=https://#/supportdesk/"+">"+"#" + issue.ref +"</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                #         # Send Notification
                #         n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                #         n_recipient     = get_object_or_404(Users,id = issue.issuer.reporting_to_id)
                #         n_action_url    = reverse('desk:issue_dashboard')
                #         n_model         = 'Issue'
                #         n_verb          = issue.ref + " - Issue Solved!"
                #         n_description   = 'Issue(#' + issue.ref +') of '+str(issue.issuer)+' has been solved by '
                #         n_is_repeated   = True
                #         notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                        
                #         mail = EmailMessage(subject, msg, settings.EMAIL_HOST_USER, [str(issue.issuer.reporting_to.email)])
                #         mail.content_subtype = "html"
                #         mail.send()
                #     except Exception as msg:
                #         return JsonResponse(str(msg), safe=False)
                messages.success(request, message)
                    
            return JsonResponse(message, safe=False)
        else:
            return JsonResponse("Invalid Data", safe=False)
    return JsonResponse("Something went wrong!", safe=False)

@csrf_exempt
@login
def issue_feedback(request):
    if request.method == 'POST':
        issue = Issue.objects.filter(id=int(request.POST['issue']))
        if issue:
            note = request.POST['note']
            issue.update(feedback_note = note)
            if issue[0].issuer.email:
                try:
                    subject = 'EBS #' + issue[0].ref + " - Issue Feedback!"
                    msg = note+" <a href=https://#/supportdesk/"+">Click Here for Detail</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                    # Send Notification
                    n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                    n_recipient     = get_object_or_404(Users,id = issue[0].issuer_id)
                    n_action_url    = reverse('desk:issue_dashboard')
                    n_model         = 'Issue'
                    n_verb          = issue[0].ref + " - Issue Feedback!"
                    n_description   = 'Resolver Feedback: '+note
                    n_is_repeated   = False
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                    
                    # mail = EmailMessage(subject, msg, settings.EMAIL_HOST_USER, [str(issue[0].issuer.email)])
                    # mail.content_subtype = "html"
                    # mail.send()
                except Exception as msg:
                    return JsonResponse(str(msg), safe=False)

            message = '#' + issue[0].ref +' - Feedback message has been sent to issuer.'
            messages.success(request, message)     
            return JsonResponse(message, safe=False)
        else:
            return JsonResponse("Invalid Data", safe=False)
    return JsonResponse("Something went wrong!", safe=False)

@login
def device_assessment_entry(request):
    if request.session.get('is_head') or request.session.get('hd_role') == "2" or request.session.get('hd_role') == "3" or request.session.get('hd_role') == "4":
        if request.method == 'POST':
            hd_issue = request.POST.get("hd_issue", None)
            assessment_for = request.POST.get("assessment_for")
            note           = request.POST.get("note")
            device_type = request.POST.get("device_type")
            device = request.POST.get("device", None)
            item = request.POST.getlist("item", None)
            question1 = True if request.POST.get("question1") else False
            question2 = True if request.POST.get("question2") else False
            question3 = True if request.POST.get("question3") else False
            emp_dpt_head = Users.objects.filter(id = assessment_for).first()
            ceo = emp_dpt_head.company.ceo_id
            emp_company = str(emp_dpt_head.company.name) if emp_dpt_head else ""
            if emp_dpt_head and emp_dpt_head.reporting_to: emp_dpt_head = emp_dpt_head.reporting_to_id
            else: emp_dpt_head = None

            ict_dpt_head = Users.objects.filter(designation__name = "Head of ICT").first()
            if ict_dpt_head: ict_dpt_head = ict_dpt_head.id
            else: ict_dpt_head = None

            ed = Users.objects.filter(designation__name = "Executive Director").first()
            if ed: ed = ed.id
            else: ed = None
            
            # if ceo: ceo = ceo.id
            
            assessment = DeviceAssessments.objects.create(
                assessment_for_id = assessment_for, assessment_by = int(request.session.get("id")),
                device_type = device_type, device = device, note = note, question1 = question1,
                question2 = question2, question3 = question3, head_of_assessment = emp_dpt_head,
                head_of_ict = ict_dpt_head, ed = ed, ceo = ceo, hd_issue_id=hd_issue
            )
            if assessment : assessment.item.set(item)
            try :
                if hd_issue := Issue.objects.filter(id=hd_issue).first() :
                    hd_issue.da_status = True
                    hd_issue.save()
            except : pass
            
            if assessment and assessment.head_of_assessment_name().email:
                try:
                    msg = "You have a 'Device Assessment' approval in pending state. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to approve or reject</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                    subject = "Device Assessment Approval"
                    # Send Notification
                    n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                    n_recipient     = get_object_or_404(Users,id = assessment.head_of_assessment)
                    n_action_url    = reverse('desk:assessment_list')
                    n_model         = 'DeviceAssessments'
                    n_verb          = "You have a 'Device Assessment' approval in pending state for "+str(assessment.assessment_for)+"."
                    n_description   = 'Assessment Note: '+note
                    n_is_repeated   = False
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                    
                    # mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, [str(assessment.head_of_assessment_name().email)])
                    # mail.content_subtype = "html"
                    # mail.send()
                except Exception as msg: messages.warning(request, str(msg))
                messages.success(request, "Device assessment successful")
            else : messages.warning(request, "Invalid Data!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        employee_list, hd_issue = Users.objects.filter(status = True), None
        device_list = AssessmentDeviceList.objects.filter(status = True)
        if issue_ref := request.GET.get('issue_ref') : hd_issue = Issue.objects.filter(ref=issue_ref).first()
        context = {
            'employee_list':employee_list,
            'device_list':device_list,
            'item_list':item_list,
            'hd_issue':hd_issue
        }         
        return render(request, 'issue/device_assesment_entry.html', context)
    else:    
        messages.warning(request, "You have no access on this page!")
        return redirect('/supportdesk/')

@login
def assessment_list(request):
    if request.session.get('is_head') or request.session.get('hd_role') == "2" or request.session.get('hd_role') == "3" or request.session.get('hd_role') == "4":
        device_list = AssessmentDeviceList.objects.filter(status = True)
        ict_dpt_head = Users.objects.filter(designation__name = "Head of ICT").first()
        if ict_dpt_head: ict_dpt_head = ict_dpt_head.id
        else: ict_dpt_head = None
        if request.method == 'POST':
            device_type = request.POST.get('device_type')
            searchDateRange = request.POST.get('searchDateRange')
            device = request.POST.get('device')
            status = request.POST.get('status')
            assessment_list = []
            if request.session.get('hd_role') == "4" or request.session["role_text"] == "Admin" or request.session["role_text"] == "Super Admin":
                if device and not device_type and not searchDateRange and not status:
                    assessment_list = DeviceAssessments.objects.filter(device = device).order_by('-id')
                elif device and device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, device_type = device_type, status = status).order_by('-id')
                elif device and device_type and not searchDateRange and not status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, device_type = device_type).order_by('-id')
                elif device and not device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, status = status).order_by('-id')
                elif not device and device_type and not searchDateRange and not status:
                    assessment_list = DeviceAssessments.objects.filter(device_type = device_type).order_by('-id')
                elif not device and device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(device_type = device_type, status = status).order_by('-id')
                elif not device and not device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(status = status).order_by('-id')
                elif not device and not device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(created_at__date__gte = from_date, created_at__date__lte = to_date).order_by('-id')
                elif not device and device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(device_type = device_type, created_at__date__gte = from_date, created_at__date__lte = to_date).order_by('-id')
                elif device and not device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(device = device, created_at__date__gte = from_date, created_at__date__lte = to_date).order_by('-id')
                elif not device and not device_type and searchDateRange and status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    if status == "1":
                        assessment_list = DeviceAssessments.objects.filter(issuer_dpt_approve_at__date__gte = from_date, issuer_dpt_approve_at__date__lte = to_date).order_by('-id')
                    elif status == "2":
                        assessment_list = DeviceAssessments.objects.filter(ict_dpt_approve_at__date__gte = from_date, ict_dpt_approve_at__date__lte = to_date).order_by('-id')
                    elif status == "4":
                        assessment_list = DeviceAssessments.objects.filter(ceo_approve_at__date__gte = from_date, ceo_approve_at__date__lte = to_date).order_by('-id')
                    elif status == "5":
                        assessment_list = DeviceAssessments.objects.filter(status = status, ceo_approve_at__date__gte = from_date, ceo_approve_at__date__lte = to_date).order_by('-id')
                    elif status == "6":
                        assessment_list = DeviceAssessments.objects.filter(status = status, canceled_at__gte = from_date, canceled_at__date__lte = to_date).order_by('-id')
                elif not device and not device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(
                        (Q(issuer_dpt_approve_at__date__gte = from_date)&Q(issuer_dpt_approve_at__date__lte = to_date))|
                        (Q(ict_dpt_approve_at__date__gte = from_date)&Q(ict_dpt_approve_at__date__lte = to_date))|
                        (Q(ceo_approve_at__date__gte = from_date)&Q(ceo_approve_at__date__lte = to_date))|
                        (Q(canceled_at__date__gte = from_date)&Q(canceled_at__date__lte = to_date))|
                        (Q(created_at__date__gte = from_date)&Q(created_at__date__lte = to_date))).order_by('-id')
            elif request.session.get('hd_role') == "2" or request.session.get('hd_role') == "3":
                if device and not device_type and not searchDateRange and not status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif device and device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, device_type = device_type, status = status, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif device and device_type and not searchDateRange and not status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, device_type = device_type, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif device and not device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(device = device, status = status, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and device_type and not searchDateRange and not status:
                    assessment_list = DeviceAssessments.objects.filter(device_type = device_type, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(device_type = device_type, status = status, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and not device_type and not searchDateRange and status:
                    assessment_list = DeviceAssessments.objects.filter(status = status, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and not device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(created_at__date__gte = from_date, created_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(device_type = device_type, created_at__date__gte = from_date, created_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif device and not device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(device = device, created_at__date__gte = from_date, created_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and not device_type and searchDateRange and status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    if status == "1":
                        assessment_list = DeviceAssessments.objects.filter(issuer_dpt_approve_at__date__gte = from_date, issuer_dpt_approve_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                    elif status == "2":
                        assessment_list = DeviceAssessments.objects.filter(ict_dpt_approve_at__date__gte = from_date, ict_dpt_approve_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                    elif status == "4":
                        assessment_list = DeviceAssessments.objects.filter(ceo_approve_at__date__gte = from_date, ceo_approve_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                    elif status == "5":
                        assessment_list = DeviceAssessments.objects.filter(status = status, ceo_approve_at__date__gte = from_date, ceo_approve_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                    elif status == "6":
                        assessment_list = DeviceAssessments.objects.filter(status = status, canceled_at__gte = from_date, canceled_at__date__lte = to_date, assessment_by = int(request.session.get('id'))).order_by('-id')
                elif not device and not device_type and searchDateRange and not status:
                    from_date = datetime.strptime(str(searchDateRange.split("-")[0].strip()), '%m/%d/%Y')
                    to_date   = datetime.strptime(str(searchDateRange.split("-")[1].strip()), '%m/%d/%Y')
                    assessment_list = DeviceAssessments.objects.filter(
                        assessment_by = int(request.session.get('id'))&
                        (Q(issuer_dpt_approve_at__date__gte = from_date)&Q(issuer_dpt_approve_at__date__lte = to_date))|
                        (Q(ict_dpt_approve_at__date__gte = from_date)&Q(ict_dpt_approve_at__date__lte = to_date))|
                        (Q(ceo_approve_at__date__gte = from_date)&Q(ceo_approve_at__date__lte = to_date))|
                        (Q(canceled_at__date__gte = from_date)&Q(canceled_at__date__lte = to_date))|
                        (Q(created_at__date__gte = from_date)&Q(created_at__date__lte = to_date))).order_by('-id')

            context = {
                'status':status,
                'ict_dpt_head':ict_dpt_head,
                'device':device,
                'device_type':device_type,
                'searchDateRange':searchDateRange,
                'assessment_list':assessment_list,
                'device_list':device_list,
            }         
            return render(request, 'issue/assessment_list.html', context)
        else:    

            # ed = Users.objects.filter(designation__name = "Executive Director").first()
            # if ed: ed = ed.id
            # else: ed = None
            
            ceo = Users.objects.values_list('id',flat = True).filter(Q(designation__name = "Chief Executive Officer")|Q(designation__name = "Chief Executive Officer")|Q(designation__name = "Chief Executive Officer"))
            
            if request.session.get('role_text') == "Admin" or request.session.get('role_text') == "Super Admin":
                assessment_list = DeviceAssessments.objects.all().order_by('status','-id')
                # assessment_list = DeviceAssessments.objects.values().all().order_by('status','-id')
            elif request.session.get('is_head'):
                if ict_dpt_head == request.session.get("id"): #Only ICT Head
                    assessment_list = DeviceAssessments.objects.all().order_by('status','-id')
                elif int(request.session.get("id")) in ceo: #only CEO
                    assessment_list = DeviceAssessments.objects.filter((Q(head_of_assessment = int(request.session.get("id"))) & Q(status = "1"))|(Q(ceo = int(request.session.get("id"))) & Q(status = "4"))).exclude(Q(status = "5")|Q(status = "6")).order_by('-id')
                # elif ed == int(request.session.get("id")): #Skip ED panel now
                #     assessment_list = DeviceAssessments.objects.filter(Q(head_of_assessment = int(request.session.get("id"))) | Q(status = "3")).exclude(Q(status = "5")|Q(status = "6")).order_by('-id')
                else: #others department head
                    assessment_list = DeviceAssessments.objects.filter(head_of_assessment = int(request.session.get("id")), status = "1").exclude(Q(status = "5")|Q(status = "6")).order_by('-id')
            else:
                assessment_list = DeviceAssessments.objects.filter(Q(assessment_for_id = int(request.session.get("id")))|Q(assessment_by = int(request.session.get("id")))|Q(head_of_assessment = int(request.session.get("id")))|Q(head_of_ict = int(request.session.get("id")))|Q(ed = int(request.session.get("id")))|Q(ceo = int(request.session.get("id")))).order_by('status','-id')
            
            context = {
                'ict_dpt_head':ict_dpt_head,
                'device_list':device_list,
                'assessment_list':assessment_list
            }         
            return render(request, 'issue/assessment_list.html', context)
    else:    
        messages.warning(request, "You have no access on this page!")
        return redirect('/supportdesk/')

@csrf_exempt
@login
def assessment_approve(request):
    if request.session.get('is_head') or request.session.get('hd_role') in ["2", "4"]:
        if request.method == 'POST':
            if 'status' and 'assessment' in request.POST:
                note        = request.POST['note']
                assessment  = int(request.POST['assessment'])
                status      = request.POST['status']
                action      = request.POST['action']
                message     = "Assessment Approval Success"
                
                assessment_obj = DeviceAssessments.objects.filter(id = assessment).exclude(Q(status = "6")|Q(status = "5"))
                if assessment_obj:
                    msg = "You have a 'Device Assessment' approval in pending state. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to approve or reject</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                    subject = "Device Assessment Approval"
                    receiver_email = None
                    
                    if status == "1" and assessment_obj[0].head_of_assessment == request.session.get("id"): #issuer/employee department head approval
                        ict_dpt_head = Users.objects.filter(designation__name = "Head of ICT").first()
                        if ict_dpt_head: ict_dpt_head = ict_dpt_head.id
                        else: ict_dpt_head = None
                        if action == "Approve":
                            if assessment_obj[0].head_of_ict_name().email: 
                                receiver_email = assessment_obj[0].head_of_ict_name().email

                            assessment_obj.update(
                                status = "2", issuer_dpt_approve_at = datetime.now(), issuer_dpt_head_note = note
                            )
                        elif action == "Reject":
                            if assessment_obj[0].assessment_by_name().email: 
                                receiver_email = assessment_obj[0].assessment_by_name().email
                                msg = "Your 'Device Assessment' approval is rejected by employee's department head. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                                subject = "Device Assessment Approval Rejected"

                            assessment_obj.update(
                                status = "6", canceled_at = datetime.now(), canceled_note = note, canceled_by = "Issuer Department Head"
                            )

                        elif action == "Approve" and request.session.get("id") == ict_dpt_head: #Only when ICT head & Department head is same person
                            if assessment_obj[0].head_of_ict_name().email: 
                                receiver_email = assessment_obj[0].head_of_ict_name().email

                            assessment_obj.update(
                                status = "3", issuer_dpt_approve_at = datetime.now(), issuer_dpt_head_note = note, ict_head_note = note
                            )

                            # Send Notification
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,id = assessment_obj[0].assessment_by)
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = subject
                            n_description   = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by ICT department head."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            

                        elif action == "Finish" and request.session.get("id") == ict_dpt_head: #Only when ICT head & Department head is same person
                            if assessment_obj[0].assessment_by_name().email: 
                                receiver_email = assessment_obj[0].assessment_by_name().email
                                msg = "Your device has been approved by ICT department head. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                                subject = "Device Assessment Approved"

                            #Email send to Nurnobi bhai temporarily for Stage requisition only
                            msg = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by ICT department head. <br> Note: "+assessment_obj[0].note+"<br><br>Approved Note: "+note+"<br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                            # Send Notification
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,employee_id = "EC00007363")
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = subject
                            n_description   = "Your device has been approved by ICT department head."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            
                            # mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail.content_subtype = "html"
                            mail.send()

                            assessment_obj.update(
                                status = "5", ict_dpt_approve_at = datetime.now(), ict_head_note = note
                            )

                    elif status == "2" and assessment_obj[0].head_of_ict == request.session.get("id"): # ICT department head approval
                        if action == "Approve":
                            if assessment_obj[0].ceo_name().email: 
                                receiver_email = assessment_obj[0].ceo_name().email

                            assessment_obj.update(
                                status = "4", ict_dpt_approve_at = datetime.now(), ict_head_note = note #skip ED approval for that status = 4
                            )

                            # Send Notification to CEO
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,id = assessment_obj[0].ceo)
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = "You have a 'Device Assessment' approval in pending state."
                            n_description   = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by ICT department head."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            

                        elif action == "Finish":
                            if assessment_obj[0].assessment_by_name().email: 
                                receiver_email = assessment_obj[0].assessment_by_name().email
                                msg = "Your device has been approved by ICT department head. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                                subject = "Device Assessment Approved"

                            #Email send to Nurnobi bhai temporarily for Stage requisition only
                            msg = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by ICT department head. <br> Note: "+assessment_obj[0].note+"<br><br>Approved Note: "+note+"<br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                            # Send Notification to resolver
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,id = assessment_obj[0].assessment_by)
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = "Your device has been approved by ICT department head."
                            n_description   = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by ICT department head."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            
                            # Send Notification to Nurnabi vai
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,employee_id = "EC00007363")
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = "Your device has been approved by ICT department head."
                            n_description   = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by ICT department head."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            
                            # mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail.content_subtype = "html"
                            mail.send()

                            assessment_obj.update(
                                status = "5", ict_dpt_approve_at = datetime.now(), ict_head_note = note
                            )

                        elif action == "Reject":
                            if assessment_obj[0].assessment_by_name().email: 
                                receiver_email = assessment_obj[0].assessment_by_name().email
                                msg = "Your 'Device Assessment' approval is rejected by employee's department head. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                                subject = "Device Assessment Approval Rejected"

                            assessment_obj.update(
                                status = "6", canceled_at = datetime.now(), canceled_note = note, canceled_by = "ICT Department Head"
                            )

                            # Send Notification to resolver
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,id = assessment_obj[0].assessment_by)
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = "Device Assessment Approval Rejected"
                            n_description   = "Your 'Device Assessment' approval is rejected by employee's department head."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                    
                    elif status == "2" and assessment_obj[0].assessment_by == request.session.get("id"):
                        subject = "Device Assessment Approved"

                        # Send Notification resolver
                        n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                        n_recipient     = get_object_or_404(Users,id = assessment_obj[0].assessment_by)
                        n_action_url    = reverse('desk:assessment_list')
                        n_model         = 'DeviceAssessments'
                        n_verb          = subject
                        n_description   = "Your device assessment for "+str(assessment_obj[0].assessment_for)+" has been approved by CEO."
                        n_is_repeated   = False
                        notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                        
                        # Send Notification
                        #Email send to Nurnobi bhai temporarily for Stage requisition only
                        msg = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by CEO. <br> Note: "+assessment_obj[0].note+"<br><br>Approved Note: "+note+"<br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                        n_recipient     = get_object_or_404(Users,employee_id = "EC00007363")
                        notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=msg, is_repeated=n_is_repeated)
                        # mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                        mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                        mail.content_subtype = "html"
                        mail.send()

                        assessment_obj.update(status="5", ict_finished_at = datetime.now())

                    # elif status == "3" and assessment_obj[0].ed == request.session.get("id"): # ED approval #skip ED approval 
                    #     if action == "Approve":
                    #         if assessment_obj[0].ceo_name().email: 
                    #             receiver_email = assessment_obj[0].ceo_name().email

                    #         assessment_obj.update(
                    #             status = "4", ed_approve_at = datetime.now(), ed_note = note
                    #         )

                    #     elif action == "Reject":
                    #         if assessment_obj[0].assessment_by_name().email: 
                    #             receiver_email = assessment_obj[0].assessment_by_name().email
                    #             msg = "Your 'Device Assessment' approval is rejected by ED. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                    #             subject = "Device Assessment Approval Rejected"

                    #         assessment_obj.update(
                    #             status = "6", canceled_at = datetime.now(), canceled_note = note, canceled_by = "ED"
                    #         )

                    elif status == "4" and assessment_obj[0].ceo == request.session.get("id"): # CEO approval
                        if action == "Approve":
                            if assessment_obj[0].ceo_name().email: 
                                receiver_email = assessment_obj[0].ceo_name().email
                                msg = "Your device has been approved by CEO. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                                subject = "Device Assessment Approved"

                            #Email send to Nurnobi bhai temporarily for Stage requisition only
                            msg = "Device assessment of "+str(assessment_obj[0].assessment_by_name())+" for "+str(assessment_obj[0].assessment_for)+"("+str(assessment_obj[0].assessment_for.employee_id)+") has been approved by CEO. <br> Note: "+assessment_obj[0].note+"<br><br>Approved Note: "+note+"<br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                            # Send Notification resolver
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,id = assessment_obj[0].assessment_by)
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = subject
                            n_description   = "Your device assessment for "+str(assessment_obj[0].assessment_for)+" has been approved by CEO."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            
                            # Send Notification
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,employee_id = "EC00007363")
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = subject
                            n_description   = msg
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                                                        
                            # mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail.content_subtype = "html"
                            mail.send()

                            assessment_obj.update(
                                status = "5", ceo_approve_at = datetime.now(), ceo_note = note
                            )
                            
                        elif action == "Reject":
                            if assessment_obj[0].assessment_by_name().email: 
                                receiver_email = assessment_obj[0].assessment_by_name().email
                                msg = "Your 'Device Assessment' approval is rejected by CEO. <br> <a href=https://#/supportdesk/device-assessment-list/"+">Click here to view</a><br><br><br>**This is system generated e-mail. Please do not reply to this e-mail."
                                subject = "Device Assessment Approval Rejected"

                            assessment_obj.update(
                                status = "6", canceled_at = datetime.now(), canceled_note = note, canceled_by = "CEO"
                            )

                            # Send Notification to resolver
                            n_sender        = get_object_or_404(Users,id = request.session.get("id"))
                            n_recipient     = get_object_or_404(Users,id = assessment_obj[0].assessment_by)
                            n_action_url    = reverse('desk:assessment_list')
                            n_model         = 'DeviceAssessments'
                            n_verb          = "Device Assessment Approval Rejected"
                            n_description   = "Your 'Device Assessment' approval for "+str(assessment_obj[0].assessment_for)+" is rejected by CEO."
                            n_is_repeated   = False
                            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                            

                    if receiver_email:
                        try:
                            # mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, ["#"])
                            mail = EmailMessage(subject, msg , settings.EMAIL_HOST_USER, [receiver_email])
                            mail.content_subtype = "html"
                            mail.send()
                        except Exception as msg:
                            return JsonResponse(str(msg), safe=False) 
                                
                    return JsonResponse(message, safe=False)

                return JsonResponse("Invalid Data", safe=False)
        return JsonResponse("Something went wrong!", safe=False)
    else:    
        return JsonResponse("You have no access on this page!", safe=False)

@csrf_exempt
@login
def device_assessment_view(request):
    assessment = DeviceAssessments.objects.values().filter(id=request.POST.get("assessment_id"))
    if assessment:
        return JsonResponse(list(assessment)[0], safe=False)
    else:    
        return JsonResponse(None, safe=False)

@login
def assessment_approved_report(request, id):
    ict_dpt_head = Users.objects.filter(designation__name = "Head of ICT", id = int(request.session.get("id"))).first()
    
    if request.session.get('role_text') == "Admin" or request.session.get('role_text') == "Super Admin" or ict_dpt_head:
        assessment = DeviceAssessments.objects.filter(Q(status = "5")|Q(status = "6"), id = id)
    else:    
        assessment = DeviceAssessments.objects.filter(Q(assessment_for_id = int(request.session.get("id")))|Q(assessment_by = int(request.session.get("id")))|Q(head_of_assessment = int(request.session.get("id")))|Q(head_of_ict = int(request.session.get("id")))|Q(ed = int(request.session.get("id")))|Q(ceo = int(request.session.get("id"))), id = id)
    if assessment:
        context = {
            'assessment': assessment[0],
            'host': str(request.scheme)+"://"+str(request.get_host()),
            }
        pdf = render_to_pdf('issue/assessment_approved_report.html', context)
        return HttpResponse(pdf, content_type='application/pdf')
    else:
        messages.warning(request, "Assessment Not Found!") 
        return redirect('desk:assessment_list')

@csrf_exempt
@login
def getUser(request):
    user = Users.objects.filter(id=request.POST.get("emp_id")).values(
                'name','employee_id', 'company__name', 'department__name','designation__name', 
                'email','reporting_to__name','reporting_to__employee_id')
    if user:
        emp = EmployeeDetails.objects.filter(personal__employee_id = user[0]['employee_id'], status = True).values(
                'personal__photo','office_mobile','unit__value').first()
        context = {
            'phone': "Phone: " + (str(emp['office_mobile']) if emp else "N/A"),
            'photo': str(emp['personal__photo']) if emp else "", 'user':list(user),
            'location': str(" ( Sitting Location: " + str(emp['unit__value']) + " ) ")  if emp and emp['unit__value'] else "",
        }
        return JsonResponse(context, safe=False)
    else: return JsonResponse(None, safe=False)

@csrf_exempt
def generate_sr_from_desk(request):
    
    return JsonResponse({'url':'/supportdesk/device-assessment-list/'}, safe=False)