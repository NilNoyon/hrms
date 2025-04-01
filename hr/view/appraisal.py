from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.http import HttpResponseRedirect
from general.decorators import login, permission
from general.models import Users, Status, Company, Branch
from datetime import timedelta, datetime
from django.contrib import messages
from notification.signals import notify
from django.utils.timezone import now
from hr.models import EmployeeDetails, Appraisal, PerformanceIndicator
 
@login
def appraisal_entry(request):
    chk_permission = permission(request, reverse('hr:appraisal_entry'))
    if chk_permission and chk_permission.view_action and chk_permission.insert_action:
        appraisee = EmployeeDetails.objects.filter(personal__employee_id=request.session.get("employee_id", None)).last()
        user, appraisal = get_object_or_404(Users, pk=request.session.get("id", "")), None
        if not appraisee :
            messages.warning(request, 'Your Employee Information not updated!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        elif not user.reporting_to_id :
            messages.warning(request, 'Your Reporting Boss is not Assaigned!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        # elif appraisee.last_date_of_appraisal and appraisee.last_date_of_appraisal > now().date() - timedelta(days=350):
        #     messages.warning(request, 'Appraisals can only be requested for employees who had their last appraisal more than 350 days ago!')
        #     return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        elif last_appraisal := Appraisal.objects.filter(appraisee=appraisee).exclude(status__in=[Status.name('Requested'), Status.name('Rejected')]).order_by('-created_at').first() : 
            if last_appraisal.created_at > now() - timedelta(days=30):
                messages.warning(request, 'An appraisal request was already made within the last 30 days!')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        elif last_appraisal := Appraisal.objects.filter(appraisee=appraisee, status__in=[Status.name('Requested'), Status.name('Rejected')]).order_by('-created_at').first() : 
            appraisal = last_appraisal

        if request.method == "POST": 
            last_appraisal_id = request.POST.get('last_appraisal_id', None)
            date_of_appraisal = request.POST.get('last_date_of_appraisal', None)
            last_date_of_appraisal = datetime.strptime(date_of_appraisal, "%d/%m/%Y") if date_of_appraisal else None
            if last_appraisal_id and Appraisal.objects.filter(id=last_appraisal_id).exists():
                appraisal = Appraisal.objects.filter(id=last_appraisal_id).first()
                appraisal.last_increment_amount = request.POST.get("last_increment_amount", None) or None
                appraisal.last_date_of_appraisal= last_date_of_appraisal
                appraisal.improvement_areas     = request.POST.get("improvement_areas", None)
                appraisal.strengths             = request.POST.get("strengths", None)
                appraisal.self_justification    = request.POST.get("self_justification", None)
                appraisal.status                = Status.name('Requested')
                appraisal.save()
                messages.success(request, 'Appraisal Request Re-Submitted!')
            else : 
                appraisal = Appraisal.objects.create(appraisee=appraisee, last_increment_amount=request.POST.get("last_increment_amount", None) or None, last_date_of_appraisal=last_date_of_appraisal, improvement_areas=request.POST.get("improvement_areas", None), strengths=request.POST.get("strengths", None), self_justification=request.POST.get("self_justification", None), status=Status.name('Requested'), created_by=get_object_or_404(Users, pk=request.session.get("id")))
                messages.success(request, 'Appraisal Request Submitted!')
            # send notification
            n_sender        = appraisal.created_by
            n_action_url    = reverse('hr:appraisal_list')
            n_model         = 'Appraisal'
            n_verb          = 'Appraisal Requested'
            n_description   = "1 new Appraisal Requested in HR"
            notify.send(n_sender, recipient=appraisal.created_by.reporting_to, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
            return redirect(reverse('hr:appraisal_entry'))
        return render(request, "hr/appraisal/entry.html", {'appraisee':appraisee, 'appraisal':appraisal})
    else: return redirect(reverse("access_denied"))

@login
def appraisal_list(request):
    chk_permission = permission(request, reverse('hr:appraisal_list'))
    if chk_permission and chk_permission.view_action :
        user_id = request.session.get("id", "")
        reporting_users = Users.objects.filter(reporting_to=user_id)
        chairman_user = Branch.objects.filter(branch_head_id=user_id).exists()
        if reporting_users.count() == 0 and not chairman_user :
            messages.warning(request, 'You don\'t have any Reporting Users!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        if request.method == "POST" :
            indicators = {
                "job-knowledge"         : request.POST.get("job-knowledge"),
                "commitment"            : request.POST.get("commitment"),
                "task-orientation"      : request.POST.get("task-orientation"),
                "attitude"              : request.POST.get("attitude"),
                "team-work"             : request.POST.get("team-work"),
                "cooperative"           : request.POST.get("cooperative"),
                "communication"         : request.POST.get("communication"),
                "pro-activeness"        : request.POST.get("pro-activeness"),
                "organizing-capability" : request.POST.get("organizing-capability"),
                "customer-orientation"  : request.POST.get("customer-orientation"),
            }
            # Create the appraisal record
            if appraisal := Appraisal.objects.filter(id=request.POST.get("appraisal_id", None)).first() :
                if request.POST.get('cahirman_user', None) == 'no' :
                    effective_from_date         = request.POST.get('effective_from_date', None)
                    appraisal.effective_from_date = datetime.strptime(effective_from_date, "%d/%m/%Y") if effective_from_date else None
                    appraisal.promoted_as       = request.POST.get('promoted_as', None)
                    appraisal.increment_amount  = request.POST.get('increment_amount', 0)
                    appraisal.coo_comments      = request.POST.get('comments', None)
                    appraisal.coo_user_id       = user_id
                    appraisal.coo_forwarded_at  = datetime.now()
                    appraisal.status            = Status.name('Forwarded')
                    appraisal.save()
                    # Add performance indicators
                    for name, score in indicators.items():
                        try : PerformanceIndicator.objects.create(appraisal=appraisal, indicator_name=name, score=int(score))
                        except : pass
                    appraisal.calculate_grand_total()
                    
                    # send notification
                    n_sender        = appraisal.coo_user
                    n_recipient     = appraisal.created_by.company.md
                    
                    n_action_url    = reverse('hr:appraisal_list')
                    n_model         = 'Appraisal'
                    n_verb          = 'Appraisal {}'.format(appraisal.status.title)
                    n_description   = "1 new Appraisal {} in HR".format(appraisal.status.title)
                    notify.send(n_sender, recipient=appraisal.created_by, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
                else : 
                    appraisal.chairman_comments     = request.POST.get('comments', None)
                    appraisal.chairman_user_id      = user_id
                    appraisal.chairman_approved_at  = datetime.now()
                    appraisal.status                = Status.name('Approved')
                    appraisal.save()
                    # send notification
                    n_sender        = appraisal.chairman_user
                    n_recipient     = appraisal.created_by
                messages.success(request, 'Appraisal Request {}!'.format(appraisal.status.title))
                if n_recipient :
                    n_action_url    = reverse('hr:appraisal_list')
                    n_model         = 'Appraisal'
                    n_verb          = 'Appraisal {}'.format(appraisal.status.title)
                    n_description   = "1 new Appraisal {} in HR".format(appraisal.status.title)
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
            else : messages.warning(request, 'No Appraisal Request Found!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        pending_status, approved_status = Status.name('Requested'), [Status.name('Forwarded'), Status.name('Approved'), Status.name('Approved')]
        if chairman_user : pending_status, approved_status = Status.name('Forwarded'), [Status.name('Approved')]
        pending_appraisals = Appraisal.objects.filter(status=pending_status).order_by('created_at')
        approved_appraisals = Appraisal.objects.filter(status__in=approved_status).order_by('-created_at')
        rejected_appraisals = Appraisal.objects.filter(status=Status.name('Rejected')).order_by('-created_at')
        if chairman_user : rejected_appraisals = rejected_appraisals.filter(chairman_user_id=user_id)
        return render(request, "hr/appraisal/list.html", {'pending_appraisals':pending_appraisals, 'approved_appraisals':approved_appraisals, 'rejected_appraisals':rejected_appraisals, 'chairman_user':chairman_user})
    else: return redirect(reverse("access_denied"))

@csrf_exempt
def get_appraisal_data(request):
    appraisal = Appraisal.objects.filter(id=request.POST.get('id', None)).first()
    performance_indicators = (
        ("job-knowledge", "Job Knowledge, Technical Knowhow & Learning Perceptions"),
        ("commitment", "Commitment Towards Task & Company"),
        ("task-orientation", "Task Orientation (On Time Delivery)"),
        ("attitude", "Attitude, Behavior & Punctuality"),
        ("team-work", "Team Work, Grow Together Attitude"),
        ("cooperative", "Cooperative & PR with Fellow Colleagues"),
        ("communication", "Communication Skill"),
        ("pro-activeness", "Pro-Activeness, Drive & Innovation"),
        ("organizing-capability", "Organizing & Controlling Capability / Leadership Capability"),
        ("customer-orientation", "Customer Orientation (Internal & External)"),
    )
    indicators, performance_data = appraisal.performance_indicators.all(), []
    for key, label in performance_indicators:
        if indicator := indicators.filter(indicator_name=key).first() :
            score = indicator.score if indicator else None
            performance_data.append({"label": label, "score": score})
    return render(request, "hr/appraisal/data.html", {'appraisal':appraisal, 'performance_data':performance_data, 'performance_indicators':performance_indicators})

@csrf_exempt
def reject_appraisal(request): 
    user_id = request.session.get("id", "")
    user = get_object_or_404(Users, pk=request.session.get("id", ""))
    if appraisal := Appraisal.objects.filter(id=request.POST.get('id', None)).first() :
        if not Company.objects.filter(md_id=user_id).exists() :
            appraisal.coo_user_id           = user_id
            appraisal.coo_forwarded_at      = datetime.now()
            appraisal.coo_comments          = request.POST.get('notes', None)
            rejected_by                     = "Dept Head"
        else : 
            appraisal.chairman_user_id      = user_id
            appraisal.chairman_approved_at  = datetime.now()
            appraisal.chairman_comments     = request.POST.get('notes', None)
            rejected_by                     = "MD"
        appraisal.status = Status.name('Rejected')
        appraisal.save()
        messages.warning(request, 'Appraisal Request {}!'.format(appraisal.status.title))
        # send notification
        n_sender        = user
        n_action_url    = reverse('hr:appraisal_list')
        n_model         = 'Appraisal'
        n_verb          = 'Appraisal Rejected'
        n_description   = "1 new Appraisal Rejected in HR by {}".format(rejected_by)
        notify.send(n_sender, recipient=appraisal.created_by, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=True)
    else : messages.warning(request, 'No Appraisal Request Found!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@csrf_exempt
def appraisal_print(request, id):
    appraisal = Appraisal.objects.filter(id=id).first()
    performance_indicators = (
        ("job-knowledge", "Job Knowledge, Technical Knowhow & Learning Perceptions"),
        ("commitment", "Commitment Towards Task & Company"),
        ("task-orientation", "Task Orientation (On Time Delivery)"),
        ("attitude", "Attitude, Behavior & Punctuality"),
        ("team-work", "Team Work, Grow Together Attitude"),
        ("cooperative", "Cooperative & PR with Fellow Colleagues"),
        ("communication", "Communication Skill"),
        ("pro-activeness", "Pro-Activeness, Drive & Innovation"),
        ("organizing-capability", "Organizing & Controlling Capability / Leadership Capability"),
        ("customer-orientation", "Customer Orientation (Internal & External)"),
    )
    indicators, performance_data = appraisal.performance_indicators.all(), []
    for key, label in performance_indicators:
        if indicator := indicators.filter(indicator_name=key).first() :
            score = indicator.score if indicator else None
            performance_data.append({"label": label, "score": score})
    return render(request, "hr/appraisal/print.html", {'appraisal':appraisal, 'performance_data':performance_data, 'performance_indicators':performance_indicators})