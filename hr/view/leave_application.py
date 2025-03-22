from hr.views import *
from django.views.decorators.cache import cache_page
from general.templatetags.data_load import is_role_assigned


def generate_app_no(company):
    year, Year  = time.strftime("%y", time.localtime()), time.strftime("%Y", time.localtime())
    last_application   = HRLeaveApplication.objects.filter(employee__company=company, created_at__year=Year).order_by('-application_no').first()
    if last_application:
        splitted_application   = last_application.application_no.split("/")
        last_application_no    = splitted_application[3]
        application_no         = str(int(last_application_no)+1).rjust(6,'0')
    else: application_no       = format( 1, '06d')
    return 'LVA/' + company.short_name+ '/' + year + '/' + application_no

@login
def leave_application(request):
    user     = get_object_or_404(Users, pk=request.session.get("id"))
    employee = EmployeeDetails.objects.filter(personal__employee_id=user.employee_id).last()
    if request.method == "POST":
        num_days, leave_type = request.POST.get("num_days", 0), request.POST.get('leave_type', None)
        allocated_leave = HRLeaveAllocation.objects.filter(employee=employee, leave__leave_type_id=leave_type).first()
        if not allocated_leave :
            messages.warning(request, "Opps! this leave type is not allocated for you.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        elif int(allocated_leave.total_balance) < int(num_days) : 
            messages.warning(request, "Opps! You don't have {} day/s leave balance for {}"
                .format(num_days, allocated_leave.leave.leave_type.short_title))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        is_post_approved = request.POST.get("is_post_approved", 0)
        duration, start_time, end_time = request.POST.get('leave_days', ''), "", ""
        if duration:
            durations   = duration.split(" - ")
            start_time  = datetime.strptime(durations[0], "%d/%m/%Y") if durations[0] else ''
            end_time    = datetime.strptime(durations[1], "%d/%m/%Y") if durations[1] else ''
        data = {
            'employee'          : employee, 'application_no' : generate_app_no(employee.company),
            'leave'             : request.POST.get('leave_type', None),
            'start_date'        : start_time, 'end_date' : end_time,
            'avail_place'       : request.POST.get("avail_place", ''),
            'reason'            : request.POST.get("reason", ''),
            'is_post_approved'  : 1 if is_post_approved else 0,
            'attachment'        : request.FILES.get('attachment'),
            'status'            : Status.name('Raised'), 
            'created_by'        : request.session.get('id'),
        }
        form = HRLeaveApplicationForm(data)
        if form.is_valid() : 
            application = form.save()
            n_recipient = application.created_by.reporting_to
            if application.created_by.reporting_to.is_department_head:
                application.reporting_boss = application.created_by.reporting_to
                application.reporting_boss_checked_at = datetime.now()
                application.status = Status.name('Forwarded')
                n_recipient = application.created_by.dept_head()
            if application.created_by.is_department_head:
                application.reporting_boss = application.created_by
                application.reporting_boss_checked_at = datetime.now()
                application.dept_head = application.created_by
                application.dept_head_checked_at = datetime.now()
                application.status = Status.name('Recommended')
                n_recipient = Users.objects.filter(Q(role__name__iexact="hr")|Q(secondary_role__contains=['HR']))
            application.save()
            allocation = application.allocation()
            allocation.applied_days += application.num_of_days
            allocation.save()
            # send notification
            n_sender        = application.created_by
            n_action_url    = reverse('hr:leave_application')
            n_model         = 'HRLeaveApplication'
            n_verb          = 'Leave Application Raised'
            n_description   = "1 new Leave Application Raised in HR"
            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                        description=n_description, is_repeated=True)
            messages.success(request, "Successfully Submitted!")
        else : ebs_bl_common.form_errors(request, form)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    template_name, today, leaves = "hr/leave/application/list.html", datetime.now(), []
    current_fiscal_year = FiscalYear.objects.filter(status=Status.name('active')).order_by('-id').first()
    HRLeaveAllocation.objects.filter(status=Status.name('active'), fiscal_year__isnull=True).update(fiscal_year=current_fiscal_year)
    allocated_leaves= HRLeaveAllocation.objects.filter(employee=employee, status=Status.name('active'), fiscal_year=current_fiscal_year)
    for lt in allocated_leaves:
        leave_type = lt.leave.leave_type 
        data = { 'id' : leave_type.id, 'remaining_days' : lt.total_balance, 'text': leave_type.short_title + str(' - ') + leave_type.description }
        leaves.append(data)
    has_approval = False
    if request.session.get('is_head', False) or is_role_assigned(request.session.get('user_roles', False), 'HR') or Users.objects.filter(reporting_to=user).values_list('id', flat=True).count() > 0 : has_approval = True
    context = { 'leaves' : leaves, 'allocated_leaves' : allocated_leaves, 'has_approval':has_approval }
    return render(request, template_name, context)

@csrf_exempt
def get_leave_applications_for_dataTable(request, list_type='', has_approval=False):
    list_query  = Q()
    user        = get_object_or_404(Users, pk=request.session.get("id"))
    employee    = EmployeeDetails.objects.filter(personal__employee_id=user.employee_id).first()

    if list_type == "myLA": list_query &= Q(employee=employee)
    elif list_type == "pending":
        if has_approval == 'True' :
            if user.is_department_head:
                list_query &= Q(Q(Q(status=Status.name("Forwarded"), employee__department=user.department) & Q(Q(employee__company=user.company)|Q(employee__company_id__in=user.secondary_company))) | Q(status=Status.name("Raised"), employee__reporting_to=employee))
            elif is_role_assigned(request.session.get('user_roles', []), "HR"): list_query &= Q(status=Status.name("Recommended"))
            else : list_query &= Q(status=Status.name("Raised"), employee__reporting_to=employee)
        else : list_query &= ~Q(status__in=[Status.name("Approved"), Status.name("Rejected")]) & Q(employee=employee)
    elif list_type == "approved": 
        if user.is_department_head: list_query &= Q(status__in=[Status.name("Approved"), Status.name("Recommended")], dept_head=user)
        elif not is_role_assigned(request.session.get('user_roles', []), "HR") and has_approval == 'True': list_query &= ~Q(status__in=[Status.name("Raised"), Status.name("Rejected")]) & Q(reporting_boss=user)
        elif is_role_assigned(request.session.get('user_roles', []), "HR") and has_approval == 'True': list_query &= Q(status=Status.name("Approved")) & Q(Q(hr=user)|Q(employee=employee))
        else : list_query &= Q(status=Status.name("Approved"), employee=employee)

    start, data_list = int(request.POST.get('start', 0)), []
    leave_list = HRLeaveApplication.objects.filter(list_query).order_by("-id")[start:start+20]
    
    for leave in leave_list:
        applicant   = leave.employee.name + " - " + leave.employee.personal.employee_id
        created_by  = ebs_bl_common.user_html(leave.created_by, 25)
        leave_description = leave.leave.description or ''
        leave_description = ebs_bl_common.datatable_center_td(leave_description)
        start_date  = ebs_bl_common.date_time_format(leave.start_date, 'date')
        end_date    = ebs_bl_common.date_time_format(leave.end_date, 'date')
        if start_date == end_date : duration = ebs_bl_common.datatable_center_td(start_date)
        else : duration = ebs_bl_common.datatable_center_td(start_date + str(' --- ') + end_date)
        num_of_days = ebs_bl_common.datatable_center_td(str(leave.num_of_days) + " Day/s")
        status      = leave.status.title.capitalize()
        if leave.status.title.lower() == 'rejected' : 
            status +=  ("<br />" + leave.rejected_by.name  + " : " + leave.reject_notes) if leave.rejected_by_id else leave.reject_notes
        status      = ebs_bl_common.datatable_center_td(status)
        created_at  = ebs_bl_common.date_time_format(leave.created_at, 'date')
        created_at += "<br />" + ebs_bl_common.date_time_format(leave.created_at, 'time')
        created_at  = ebs_bl_common.datatable_center_td(created_at)
        if list_type == "pending" and has_approval == 'True' :
            action  = '<a href="#leaveModal" data-id="'+str(leave.id)+'" class="leave_info h4 text-success approve-btn" ><i class="ti-check-box"></i></a>'
            action += '<a href="#leaveModal" data-id="'+str(leave.id)+'" class="leave_info h4 text-danger reject-btn m-l-10" ><i class="far fa-window-close"></i></a>'
        else : action = ''
        data = [leave.application_no, applicant, leave_description, duration, num_of_days, status, created_by, created_at, action]
        if list_type == "myLA" : 
            data.remove(applicant)
            data.remove(created_by)
        data_list.append(data)

    return JsonResponse(data_list, safe=False)


@csrf_exempt
def leave_application_approval(request):
    appplication_id = request.POST.get('id', None)
    status, notify_user = request.POST.get('status', None), False
    user    = get_object_or_404(Users, pk=request.session.get("id"))
    application = HRLeaveApplication.objects.get(id=appplication_id)
    if status == 'reject' :
        application.rejected_by     = user
        application.reject_at       = datetime.now()
        application.reject_notes    = request.POST.get('notes', None)
        application.status          = Status.name('Rejected')
        application.save()

        allocation = application.allocation()
        allocation.applied_days -= application.num_of_days
        allocation.save()
        n_recipient, notify_user = application.created_by, True
    else :
        dept_heads = Users.objects.filter(Q(department=application.employee.department, is_department_head=True) & Q(Q(secondary_company__contains=[application.employee.company_id])|Q(company=application.employee.company)))
        user_roles = [user.role.name] + (user.secondary_role if user.secondary_role else [])
        if user.is_department_head :
            application.status, notify_user = Status.name('Recommended'), True
            application.dept_head = user
            application.dept_head_checked_at = datetime.now()
            n_recipient = Users.objects.filter(Q(role__name__iexact="hr")|Q(secondary_role__contains=['HR']))
            if user == application.created_by.reporting_to :
                application.reporting_boss = user
                application.reporting_boss_checked_at = datetime.now()
        elif user == application.created_by.reporting_to :
            application.status, notify_user = Status.name('Forwarded'), True
            application.reporting_boss = user
            application.reporting_boss_checked_at = datetime.now()
            n_recipient = dept_heads
        elif is_role_assigned(user_roles, "HR") :
            application.status, application.hr = Status.name('Approved'), user
            n_recipient, notify_user = application.created_by, True
            application.hr_checked_at = datetime.now()
            
            allocation = application.allocation()
            allocation.applied_days -= application.num_of_days
            allocation.availed_days += application.num_of_days
            allocation.save()
    
    application.save()
    
    # send notification
    if notify_user :
        n_sender, n_model = user, 'HRLeaveApplication'
        n_action_url    = reverse('hr:leave_application')
        n_verb          = 'Leave Application ' + application.status.title.capitalize()
        n_description   = "1 new Leave Application " + application.status.title.capitalize() + " in HR"
        notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, 
            model=n_model, verb=n_verb, description=n_description, is_repeated=True)
    
    return JsonResponse({'status': application.status.title.capitalize()})