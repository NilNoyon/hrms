import random
from hr.forms import HRManPowerBudgetForm
from hr.models import HRManPowerBudget
from hr.views import *

                
def unique_shortname(obj, text, limit):
    short_name = text[:4]
    while obj.filter(short_name=short_name).last():
        short_name = text[:2] + ''.join((random.choice(text) for i in range(limit-2)))
    return short_name

@login
def mp_budget(request):
    template_name = "hr/mp_budget/form.html"
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    
    if user.company.ceo_id == int(request.session.get('id')): approve_query = Q(Q(status=Status.name('authorized'))|Q(status=Status.name('approved')))
    elif user.company.md_id == int(request.session.get('id')): approve_query = Q(status=Status.name('approved'))
    else: approve_query = Q(Q(status=Status.name('approved'))|Q(status=Status.name('authorized')),company=user.company,department=user.department)
    if is_role_assigned(request.session["user_roles"], "HR"): approve_query = Q(Q(status=Status.name('approved'))|Q(status=Status.name('authorized')))
    
    if user.company.ceo_id == int(request.session.get('id')): query = Q(status=Status.name('raised'))
    elif user.company.md_id == int(request.session.get('id')): query = Q(status=Status.name('authorized'))
    else: query = Q(Q(status=Status.name('reject'))|Q(status=Status.name('raised'))|Q(status=Status.name('started')),company=user.company,department=user.department)
    if is_role_assigned(request.session["user_roles"], "HR"): query = Q(Q(status=Status.name('reject'))|Q(status=Status.name('raised'))|Q(status=Status.name('started')))
    total_approved  = HRManPowerBudget.objects.filter(approve_query).order_by('budget_year','department',"-id").distinct('budget_year','department').count()
    total_pending  = HRManPowerBudget.objects.filter(query).order_by('budget_year','department',"-id").distinct('budget_year','department').count()
    
    emp_details = []
    if user and (is_role_assigned(request.session['user_roles'], 'HR') or user.sc_user_level() in [4,5]):
        departments     = Departments.objects.all()
        designations    = Designations.objects.all()
    else:
        emp_details =  EmployeeDetails.objects.filter(personal__employee_id=request.session.get('employee_id')).last()
        employee_list = EmployeeDetails.objects.filter(department=emp_details.department)
        department_list = employee_list.order_by('department').distinct('department')
        departments = [{'id':i.department_id, 'name': i.department.name} for i in department_list]
        designation_list = employee_list.order_by('designation').distinct('designation')
        designations = [{'id':i.designation_id, 'name': i.designation.name} for i in designation_list]
    budget_year = HRManPowerBudget.objects.distinct('budget_year')
    context={
        'total_pending': total_pending, 'total_approved': total_approved,'company_list':Company.objects.all(),'company_id': int(request.session.get('company_id')), 'department_list':departments, 'department_id':emp_details.department_id if emp_details else None,'designation_list': designations,
        'all_department': Departments.objects.all(),'budget_year':budget_year, 'hr_roles': is_role_assigned(request.session['user_roles'], 'HR')
    }
    return render(request, template_name, context)

@login
def mp_budget_create(request):
    if request.method == "POST":
        user = get_object_or_404(Users, id=int(request.session.get('id')))
        if request.POST.get('submit_type') == 'submit': status = Status.name('Raised')
        if request.POST.get('submit_type') == 'save': status = Status.name('Started')
        budget_year = request.POST.get('budget_year')
        company = request.POST.get('company')
        department = request.POST.get('department')
        serial = request.POST.getlist('serial')
        serial = [int(i) for i in serial]
        success = False
        for i in serial:
            designation = request.POST.get(f'designation[{i}]')
            try: designation = int(designation)
            except: designation, created = Designations.objects.get_or_create(name=designation,short_name=unique_shortname(Designations.objects, str(designation).upper(), 4))
            person_limit = request.POST.get(f'person_limit[{i}]')
            value_limit = request.POST.get(f'value_limit[{i}]')
            data = {
                'budget_year':budget_year,'company':company or user.company,'department': department or user.department,'designation':designation,
                'manpower_limit_qty':person_limit,'manpower_limit_value':value_limit,
                'created_by':request.session.get('id'), 'status': status
            }
            mp_budget_form = HRManPowerBudgetForm(data)
            if mp_budget_form.is_valid():
                mpb = mp_budget_form.save()
                # if mpb.created_by_id == mpb.company.ceo_id and mpb and mpb.status == Status.name('Raised'):
                #     mpb.status = Status.name('Authorized')
                #     mpb.ceo = int(request.session.get('id'))
                #     mpb.ceo_action_at = datetime.now()
                #     mpb.save()
                #     ebs_bl_approval.log_entry(mpb, mpb.budget_year, mpb.created_by, '', mpb.status, CommonMaster.get_or_create_name('Man Power Budget Raised and Authorized By CEO'))
                #     n_recipient     = mpb.company.md
                #     n_sender        = mpb.created_by
                #     n_action_url    = reverse('hr:mp_budget')
                #     n_model         = 'Man Power Budget'
                #     n_verb          = 'Man Power Budget Waiting for approval'
                #     n_description   = "1 new Man Power Budget Raised By CEO"
                #     notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                #                 description=n_description, is_repeated=True)
                # if mpb.created_by_id == mpb.company.md_id and mpb and mpb.status == Status.name('Raised'):
                #     mpb.status = Status.name('Approved')
                #     mpb.md = int(request.session.get('id'))
                #     mpb.md_action_at = datetime.now()
                #     mpb.save()
                #     ebs_bl_approval.log_entry(mpb, mpb.budget_year, mpb.created_by, '', mpb.status, CommonMaster.get_or_create_name('Man Power Budget Raised and Approved By CEO'))
      
                if mpb and mpb.status == Status.name('Started'):    ebs_bl_approval.log_entry(mpb, mpb.budget_year, mpb.created_by, '', mpb.status, CommonMaster.get_or_create_name('Man Power Budget Started'))
                if mpb and mpb.created_by_id != mpb.company.md_id and mpb.created_by_id != mpb.company.ceo_id and  mpb.status == Status.name('Raised'):     
                    ebs_bl_approval.log_entry(mpb, mpb.budget_year, mpb.created_by, '', mpb.status, CommonMaster.get_or_create_name('Man Power Budget Raised'))
                    n_recipient     = mpb.company.ceo
                    n_sender        = mpb.created_by
                    n_action_url    = reverse('hr:mp_budget')
                    n_model         = 'Man Power Budget'
                    n_verb          = 'Man Power Budget Waiting for approval'
                    n_description   = "1 new Man Power Budget Raised"
                    notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                                description=n_description, is_repeated=True)
                success = True
        if success: messages.success(request, 'Man Power Budget Stored.')
        else: messages.warning(request, 'Man Power Budget Failed.')

    return redirect('hr:mp_budget')

@csrf_exempt
def get_mp_budget_details(request):
    budget_year = request.POST.get('budget_year')
    department  = request.POST.get('department_id')
    mp_budget_list = HRManPowerBudget.objects.filter(budget_year=budget_year, department=department)
    user = Users.objects.filter(id=int(request.session.get('id'))).first()

    emp_details = []
    if user and is_role_assigned(request.session['user_roles'], 'HR'):
        departments     = Departments.objects.all()
        designations    = Designations.objects.all()
    else:
        emp_details =  EmployeeDetails.objects.filter(personal__employee_id=request.session.get('employee_id')).last()
        employee_list = EmployeeDetails.objects.filter(department=emp_details.department)
        department_list = employee_list.order_by('department').distinct('department')
        departments = [{'id':i.department_id, 'name': i.department.name} for i in department_list]
        designation_list = employee_list.order_by('designation').distinct('designation')
        designations = [{'id':i.designation_id, 'name': i.designation.name} for i in designation_list]
    budget_year = HRManPowerBudget.objects.distinct('budget_year')
    template_name = "hr/mp_budget/mp_budget_edit.html"
    context={'mp_budget_list':mp_budget_list,'company_list':Company.objects.all(),'company_id': int(request.session.get('company_id')), 'department_list':departments, 'department_id':emp_details.department_id if emp_details else None,'designation_list': designations}
    return render(request, template_name, context)

@csrf_exempt
def mpb_view(request):
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    approval = False
    budget_year = request.POST.get('budget_year')
    department  = request.POST.get('department_id')
    mp_budget_list = HRManPowerBudget.objects.filter(budget_year=budget_year, department=department)
    mp_budget_list_dist = mp_budget_list.order_by('department').distinct('department').last()
    if user.company.ceo_id == int(request.session.get('id')) and mp_budget_list_dist.status == Status.name('Raised'): approval = True
    elif user.company.md_id == int(request.session.get('id')) and mp_budget_list_dist.status == Status.name('Authorized'): approval = True
    template_name = "hr/mp_budget/view.html"
    context={'mp_budget_list':mp_budget_list,'approval':approval}
    return render(request, template_name, context)

@csrf_exempt
def mp_budget_approval(request):
    if request.method == "POST":
        user = Users.objects.filter(id=int(request.session.get('id'))).first()
        if request.POST.get('submit_type') == 'approve' and user.company.ceo_id == int(request.session.get('id')): status = Status.name('Authorized')
        if request.POST.get('submit_type') == 'approve' and user.company.md_id == int(request.session.get('id')): status = Status.name('Approved')
        if request.POST.get('submit_type') == 'reject': status = Status.name('Rejected')
        budget_year = request.POST.get('budget_year')
        department = request.POST.get('department')
        notes = request.POST.get('notes')
       
        if user.company.ceo_id == int(request.session.get('id')):HRManPowerBudget.objects.filter(budget_year=budget_year,department=department).update(ceo_id=int(request.session.get('id')),ceo_notes=notes,ceo_action_at=datetime.now(),status=status)
        if user.company.md_id == int(request.session.get('id')):HRManPowerBudget.objects.filter(budget_year=budget_year,department=department).update(md_id=int(request.session.get('id')),md_notes=notes,md_action_at=datetime.now(),status=status)
        for i in HRManPowerBudget.objects.filter(budget_year=budget_year,department=department):
            if i.status == Status.name('Authorized'): 
                ebs_bl_approval.log_entry(i, i.budget_year, i.ceo, '', i.status, CommonMaster.get_or_create_name('Man Power Budget Authorized By CEO'))  
                n_recipient,msg,desc = user.company.md,"Waiting for approval","Authorized"
            if i.status == Status.name('Approved'): 
                ebs_bl_approval.log_entry(i, i.budget_year, i.md, '', i.status, CommonMaster.get_or_create_name('Man Power Budget Approved By MD'))
                n_recipient,msg,desc = i.created_by,"Approved By MD","Approved"
            if i.status == Status.name('Rejected') and user.company.md_id == int(request.session.get('id')): 
                ebs_bl_approval.log_entry(i, i.budget_year, i.md, '', i.status, CommonMaster.get_or_create_name('Man Power Budget Rejected By MD'))
                n_recipient,msg,desc = i.created_by,"Rejected By MD","Rejected"
            if i.status == Status.name('Rejected') and user.company.ceo_id == int(request.session.get('id')): 
                ebs_bl_approval.log_entry(i, i.budget_year, i.ceo, '', i.status, CommonMaster.get_or_create_name('Man Power Budget Rejected By CEO'))
                n_recipient,msg,desc = i.created_by,"Rejected By CEO","Rejected"
            n_recipient     = n_recipient
            n_sender        = user
            n_action_url    = reverse('hr:mp_budget')
            n_model         = 'Man Power Budget'
            n_verb          = 'Man Power Budget '+str(msg)
            n_description   = "1 new Man Power Budget "+str(desc)
            notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                        description=n_description, is_repeated=True)
        messages.success(request, 'Man Power Budget Updated.')
        return redirect('hr:mp_budget')

@csrf_exempt
def mp_budget_edit(request):
    if request.method != "POST":
        return
    if request.POST.get('submit_type') == 'submit': status = Status.name('Raised')
    if request.POST.get('submit_type') == 'save': status = Status.name('Started')
    budget_year = request.POST.get('budget_year')
    company = request.POST.get('company')
    department = request.POST.get('department')
    serial = request.POST.getlist('serial')
    serial = [int(i) for i in serial]
    success = False
    for i in serial:
        designation = request.POST.get(f'designation[{i}]')
        person_limit = request.POST.get(f'person_limit[{i}]')
        value_limit = request.POST.get(f'value_limit[{i}]')
        instance = HRManPowerBudget.objects.filter(budget_year=budget_year,department=department,designation=designation,id=int(i)).first()

        data = {
            'budget_year':budget_year,'company':company,'department':department,'designation':designation,
            'manpower_limit_qty':person_limit,'manpower_limit_value':value_limit,'status': status,
        }
        if instance: 
            data["updated_by"] = request.session.get('id')
            data["updated_at"] = datetime.now()
            mp_budget_form = HRManPowerBudgetForm(data, instance=instance)
        else: 
            data["created_by"] = request.session.get('id')
            mp_budget_form = HRManPowerBudgetForm(data)
        if mp_budget_form.is_valid():
            mpb = mp_budget_form.save()
            if mpb and mpb.status == Status.name('Started'):    ebs_bl_approval.log_entry(mpb, mpb.budget_year, mpb.created_by, '', mpb.status, CommonMaster.get_or_create_name('Man Power Budget Started'))
            if mpb and mpb.status == Status.name('Raised'): 
                ebs_bl_approval.log_entry(mpb, mpb.budget_year, mpb.created_by, '', mpb.status, CommonMaster.get_or_create_name('Man Power Budget Raised'))
                n_recipient     = mpb.company.ceo
                n_sender        = mpb.created_by
                n_action_url    = reverse('hr:mp_budget')
                n_model         = 'Man Power Budget'
                n_verb          = 'Man Power Budget Waiting for approval'
                n_description   = "1 new Man Power Budget Raised"
                notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb,
                            description=n_description, is_repeated=True)
            success = True
    if success: messages.success(request, 'Man Power Budget Updated.')
    else: messages.warning(request, 'Man Power Budget Failed.')
    return redirect('hr:mp_budget')

@csrf_exempt
def get_mp_budget_for_datatable(request, tab_name=None):
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    if tab_name == "approved":
        if user.company.ceo_id == int(request.session.get('id')): query = Q(Q(status=Status.name('authorized'))|Q(status=Status.name('approved')))
        elif user.company.md_id == int(request.session.get('id')): query = Q(status=Status.name('approved'))
        else: query = Q(Q(status=Status.name('approved'))|Q(status=Status.name('authorized')),company=user.company,department=user.department)
        if is_role_assigned(request.session["user_roles"], "HR"): query = Q(Q(status=Status.name('approved'))|Q(status=Status.name('authorized')))
    
    if tab_name == "pending":
        if user.company.ceo_id == int(request.session.get('id')): query = Q(status=Status.name('raised'))
        elif user.company.md_id == int(request.session.get('id')): query = Q(status=Status.name('authorized'))
        else: query = Q(Q(status=Status.name('reject'))|Q(status=Status.name('raised'))|Q(status=Status.name('started')),company=user.company,department=user.department)
        if is_role_assigned(request.session["user_roles"], "HR"): query = Q(Q(status=Status.name('reject'))|Q(status=Status.name('raised'))|Q(status=Status.name('started')))
    
    department     = request.POST.get('department', None)
    if department  : query &= Q(department=department)
    designation     = request.POST.get('designation', None)
    if designation  : query &= Q(designation=designation)
    company       = request.POST.get('company', None)
    if company    : query &= Q(company=company)

    start_date    = request.POST.get('start_date', '')
    end_date      = request.POST.get('end_date', '')
    if start_date or end_date:
        start_date          = datetime.strptime(start_date, "%Y-%m-%d")
        end_date            = datetime.strptime(end_date, "%Y-%m-%d")
        end_date            = end_date + timedelta(days=1)
        query               &= Q(created_at__gte=start_date, created_at__lte=end_date)


    start       = int(request.POST.get('start', 0))
    mp_budget_list           = HRManPowerBudget.objects.filter(query).order_by('budget_year','department',"-id").distinct('budget_year','department')[start:start + 20]
    data_list   = []
    for i in mp_budget_list:
        total = HRManPowerBudget.objects.filter(budget_year=i.budget_year,department=i.department).aggregate(mp_qty=Sum('manpower_limit_qty'),mp_value=Sum('manpower_limit_value'))
        budget_year     = i.budget_year if i.budget_year else ""
        company         = i.company.short_name if i.company else "N/A"
        department      = i.department.name if  i.department else "N/A"
        manpower_limit_qty    = total["mp_qty"] if total["mp_qty"] else ""
        manpower_limit_value  = total["mp_value"] if total["mp_value"] else ""
        created_at      = i.created_at.strftime("%d-%b-%Y %I:%M %p").upper() if i.created_at else ""
        status          = i.status.title if i.status else "N/A"
        created_by      = '<a href="#aboutModal" data-toggle="modal" data-id="' + str(i.created_by_id) + '" class="user_info text-info" data-target="#userModal">' + i.created_by.name + '</a>' if i.created_by else 'N/A'
        action          = ""
        # edit_url        = reverse('hr:mp_budget_edit', kwargs={'id': i.id})
        action          += '<a href="#" class="h4 m-r-10 text-success view_mp_budget" data-budget_year='+str(i.budget_year)+' data-department='+str(i.department_id)+' title="View MP Budget"><i class="ti-eye"></i></a>'

        if i.created_by_id == int(request.session.get('id')) and i.status not in [Status.name('Approved') ,Status.name('authorized'),Status.name('Raised')]:
            action          += '<a href="#" class="h4 m-r-10 text-success edit_mp_budget" data-budget_year='+str(i.budget_year)+' data-department='+str(i.department_id)+' title="Edit MP Budget"><i class="ti-pencil-alt"></i></a>'
        # action          = ebs_bl_common.action_html(action_url=edit_url, color_text='text-success', icon='ti-pencil-alt', title_text='Edit order')
        data = [budget_year, company, department,manpower_limit_qty,manpower_limit_value,status,created_by,created_at, action]
        data_list.append(data)
    return JsonResponse(data_list, safe=False)

@csrf_exempt
def delete_mp_budget(request):
    id = request.POST.get('id')
    HRManPowerBudget.objects.filter(id=int(id)).delete()
    return JsonResponse('deleted', safe=False)

@csrf_exempt
def check_exists_mp_budget(request):
    budget_year = request.POST.get('budget_year')
    company = request.POST.get('company')
    department = request.POST.get('department')
    operation = request.POST.get('operation')
    budget = HRManPowerBudget.objects.filter(budget_year=budget_year,company=company,department=department).exclude(status=Status.name('Started'))
    # if budget.status in [Status.name('Started'), Status.name('Raised')]:
    #     data = {
    #         'id':budget.id,
    #         'manpower_limit_qty':budget.manpower_limit_qty,
    #         'manpower_limit_value':budget.manpower_limit_value,
    #         'msg':'Editable'
    #     }
    msg = "exists" if budget else "None"
    return JsonResponse(msg, safe=False)