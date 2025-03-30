from hr.forms import HREmployeeRecruitmentForm
from hr.models import HREmployeeRecruitment, EmployeeDetails
from hr.views import *

@csrf_exempt
def get_employee_data(request):
    query       = Q()
    if company := request.GET.get('company', None)          : query &= Q(branch_id=company)
    if department := request.GET.get('department', None)    : query &= Q(department_id=department)
    if designation := request.GET.get('designation', None)  : query &= Q(designation_id=designation)
    if category_list := request.GET.getlist('category[]', None) : query &= Q(employee_category_id__in=category_list)
    if text := request.GET.get('q[term]', None):
        text = text.strip()
        query &= Q(Q(personal__first_name__icontains=text)|
                   Q(personal__last_name__icontains=text)|
                   Q(personal__employee_id__icontains=text))
    emp_list    = EmployeeDetails.objects.filter(query)
    employee_list = [{'id':i.id, 'text': str(i.personal.name) +" ("+str(i.personal.employee_id)+")"} for i in emp_list]
    return JsonResponse({'employee_list':employee_list}, safe=False)

@login
def recruitment(request):
    template_name = "hr/recruitment/form.html"
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    
    if user.branch.branch_head == int(request.session.get('id')): approve_query = Q(Q(status=Status.name('authorized'))|Q(status=Status.name('approved')), skip_ceo_approval=False)
    elif user.branch.branch_head == int(request.session.get('id')): approve_query = Q(status=Status.name('approved'))
    else: approve_query = Q(Q(status=Status.name('approved'))|Q(status=Status.name('authorized')),created_by_id=int(request.session.get('id')))
    
    
    if user.branch.branch_head == int(request.session.get('id')): query = Q(status=Status.name('raised'), skip_ceo_approval=False)
    elif user.branch.branch_head == int(request.session.get('id')): query = Q(Q(status=Status.name('authorized'))|Q(status=Status.name('raised'), skip_ceo_approval=True))
    else: query = Q(Q(status=Status.name('rejected'))|Q(status=Status.name('raised'))|Q(status=Status.name('started')),created_by_id=int(request.session.get('id')))
    total_approved  = HREmployeeRecruitment.objects.filter(approve_query).order_by('recruit_year','department',"-id").count()
    total_pending  = HREmployeeRecruitment.objects.filter(query).order_by('recruit_year','department',"-id").count()
    
    emp_details = []
    if user and user.sc_user_level() in [4, 5]:
        departments     = Departments.objects.all()
        designations    = Designations.objects.all()
    else:
        emp_details   = EmployeeDetails.objects.filter(personal__employee_id=request.session.get('employee_id')).last()
        employee_list = EmployeeDetails.objects.filter(Q(id=emp_details.id)|Q(reporting_to=emp_details.id))
        department_list = employee_list.order_by('department').distinct('department')
        departments = [{'id':i.department_id, 'name': i.department.name} for i in department_list]
        designation_list = employee_list.order_by('designation').distinct('designation')
        designations = [{'id':i.designation_id, 'name': i.designation.name} for i in designation_list]
    recruit_year = HREmployeeRecruitment.objects.distinct('recruit_year')
    context={
        'total_pending': total_pending, 'total_approved': total_approved,'company_list':Branch.objects.filter(company_id=request.session.get('company_id')),'company_id': int(request.session.get('branch_id')) if request.session.get('branch_id') else '', 'department_list':departments, 'department_id':emp_details.department_id if emp_details else None,'designation_list': designations,
        'all_department': Departments.objects.all(),'recruit_year':recruit_year
    }
    return render(request, template_name, context)


@login
def recruitment_create(request):
    if request.method == "POST":
        if request.POST.get('submit_type') == 'submit': status = Status.name('Raised')
        if request.POST.get('submit_type') == 'save': status = Status.name('Started')
        request.POST = request.POST.copy()
        request.POST["created_by"] = request.session.get('id')
        request.POST["status"] = status
        recruitment_id = request.POST.get('recruitment_id')
        instance = HREmployeeRecruitment.objects.filter(id=recruitment_id).first() if recruitment_id else None
        recruit_form = HREmployeeRecruitmentForm(request.POST, instance=instance)  if instance else HREmployeeRecruitmentForm(request.POST)
        if recruit_form.is_valid():
            recruitment = recruit_form.save()
            if recruitment and recruitment.status == Status.name('Started'):    ebs_bl_approval.log_entry(recruitment, recruitment.recruit_year, recruitment.created_by, '', recruitment.status, CommonMaster.get_or_create_name('Recruitment Started'))
            if recruitment and recruitment.status == Status.name('Raised'):     ebs_bl_approval.log_entry(recruitment, recruitment.recruit_year, recruitment.created_by, '', recruitment.status, CommonMaster.get_or_create_name('Recruitment Raised'))
            messages.success(request, 'Recruitment Updated.') if instance else messages.success(request, 'Recruitment Stored.')
        else: ebs_bl_common.form_errors(request, recruit_form)
    return redirect('hr:recruitment')


@csrf_exempt
def recruit_view(request):  # sourcery skip: avoid-builtin-shadow
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    approval = False
    id  = request.POST.get('id')
    recruit = HREmployeeRecruitment.objects.filter(id=id).first()
    if user.company.ceo_id == int(request.session.get('id')) and recruit.status == Status.name('raised'): approval = True
    elif user.company.md_id == int(request.session.get('id')) and recruit.status in [Status.name('raised'),Status.name('authorized')]: approval = True
    template_name = "hr/recruitment/view.html"
    context={'recruit':recruit,'approval':approval}
    return render(request, template_name, context)


@csrf_exempt
def get_check_man_power_budget(request):  # sourcery skip: avoid-builtin-shadow
    recruit_year        = int(request.POST.get('recruit_year',0))
    company             = int(request.POST.get('company',0))
    department          = int(request.POST.get('department',0))
    designation         = int(request.POST.get('designation',0))
    negotiated_salary   = int(request.POST.get('negotiated_salary',0))
    recruitment_id      = request.POST.get('recruitment_id',None)
    
    mp_budget = HRManPowerBudget.objects.filter(budget_year=recruit_year,company=company,department=department,designation=designation).first()
    if recruitment_id: recruit = HREmployeeRecruitment.objects.filter(recruit_year=recruit_year,company_id=company,department=department,designation=designation).exclude(id=int(recruitment_id))
    else: recruit = HREmployeeRecruitment.objects.filter(recruit_year=recruit_year,company_id=company,department=department,designation=designation)
    recruited = recruit.count()+1
    recruited_value = recruit.aggregate(negotiated_salary=Sum('negotiated_salary'))
    status = True
    if recruit and (recruited > mp_budget.manpower_limit_qty or float(recruited_value["negotiated_salary"])+float(negotiated_salary) > float(mp_budget.manpower_limit_value)): status = False
    elif float(negotiated_salary) > float(mp_budget.manpower_limit_value): status = False
    return JsonResponse(status, safe=False)

@csrf_exempt
def get_check_man_power_budget_designation_wise(request):
    recruit_year        = int(request.POST.get('recruit_year',0))
    company             = int(request.POST.get('company',0))
    department          = int(request.POST.get('department',0))
    designation         = int(request.POST.get('designation',0))
    recruitment_id      = request.POST.get('recruitment_id',None)
    
    mp_budget = HRManPowerBudget.objects.filter(budget_year=recruit_year,company=company,department=department,designation=designation, status=Status.name('approved')).first()
    if recruitment_id: recruit = HREmployeeRecruitment.objects.filter(recruit_year=recruit_year,company_id=company,department=department,designation=designation).exclude(id=int(recruitment_id))
    else: recruit = HREmployeeRecruitment.objects.filter(recruit_year=recruit_year,company_id=company,department=department,designation=designation)
    recruited = recruit.count()+1
    print("mp_budget: ", mp_budget)
    print("recruit: ", recruit)
    status = False if recruit and recruited > mp_budget.manpower_limit_qty else True
    recruited_value = recruit.aggregate(negotiated_salary=Sum('negotiated_salary'))
    print("recruited_value: ", recruited_value)
    data={
        'status': status,
        'manpower_limit_value': (float(mp_budget.manpower_limit_value) - (float(recruited_value["negotiated_salary"]) if recruited_value['negotiated_salary'] else 0)) if mp_budget else 0,
        'mp_budget': True if mp_budget else False
    }
    return JsonResponse(data, safe=False)

@csrf_exempt
def recruit_edit(request):  # sourcery skip: avoid-builtin-shadow
    id  = request.POST.get('id')
    recruit = list(HREmployeeRecruitment.objects.values('name','company','recruit_year','recruitment_type','department','designation','replacement_of','negotiated_salary','interviewr_comments','skip_ceo_approval').filter(id=id))
    return JsonResponse(recruit, safe=False)



@csrf_exempt
def recruit_approval(request):  # sourcery skip: avoid-builtin-shadow
    if request.method != "POST":
        return
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    if request.POST.get('submit_type') == 'approve' and user.company.ceo_id == int(request.session.get('id')): status = Status.name('Authorized')
    if request.POST.get('submit_type') == 'approve' and user.company.md_id == int(request.session.get('id')): status = Status.name('Approved')
    if request.POST.get('submit_type') == 'reject': status = Status.name('Rejected')
    id  = request.POST.get('recruitment_id')

    notes = request.POST.get('notes')
    recruitment = HREmployeeRecruitment.objects.filter(id=id)
    if user.company.ceo_id == int(request.session.get('id')):recruitment.update(ceo_id=int(request.session.get('id')),ceo_notes=notes,ceo_action_at=datetime.now(),status=status)
    if user.company.md_id == int(request.session.get('id')):recruitment.update(md_id=int(request.session.get('id')),md_notes=notes,md_action_at=datetime.now(),status=status)
    recruitment = recruitment.last()
    if recruitment.status == Status.name('Authorized'): ebs_bl_approval.log_entry(recruitment, recruitment.recruit_year, recruitment.ceo, '', recruitment.status, CommonMaster.get_or_create_name('Recruitment Authorized By CEO'))
    if recruitment.status == Status.name('Approved'): ebs_bl_approval.log_entry(recruitment, recruitment.recruit_year, recruitment.md, '', recruitment.status, CommonMaster.get_or_create_name('Recruitment Approved By MD'))
    if recruitment.status == Status.name('Rejected') and user.company.md_id == int(request.session.get('id')): ebs_bl_approval.log_entry(recruitment, recruitment.recruit_year, recruitment.md, '', recruitment.status, CommonMaster.get_or_create_name('Recruitment Rejected By MD'))
    if recruitment.status == Status.name('Rejected') and user.company.ceo_id == int(request.session.get('id')): ebs_bl_approval.log_entry(recruitment, recruitment.recruit_year, recruitment.ceo, '', recruitment.status, CommonMaster.get_or_create_name('Recruitment Rejected By CEO'))
    messages.success(request, 'Recruitment Updated.')
    return redirect('hr:recruitment')


@csrf_exempt
def get_recruit_for_datatable(request, tab_name=None):
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    if tab_name == "approved":
        if user.company.ceo_id == int(request.session.get('id')): query = Q(Q(status=Status.name('authorized'))|Q(status=Status.name('approved')), skip_ceo_approval=False)
        elif user.company.md_id == int(request.session.get('id')): query = Q(status=Status.name('approved'))
        else: query = Q(Q(status=Status.name('approved'))|Q(status=Status.name('authorized')),created_by_id=int(request.session.get('id')))
    
    if tab_name == "pending":
        if user.company.ceo_id == int(request.session.get('id')): query = Q(status=Status.name('raised'), skip_ceo_approval=False)
        elif user.company.md_id == int(request.session.get('id')): query = Q(Q(status=Status.name('authorized'))|Q(status=Status.name('raised'), skip_ceo_approval=True))
        else: query = Q(Q(status=Status.name('rejected'))|Q(status=Status.name('raised'))|Q(status=Status.name('started')),created_by_id=int(request.session.get('id')))
    
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
    recruitment_list           = HREmployeeRecruitment.objects.filter(query).order_by('recruit_year','department',"-id")[start:start + 20]
    data_list   = []
    for i in recruitment_list:
        recruit_year        = i.recruit_year if i.recruit_year else ""
        company             = i.company.short_name if i.company else "N/A"
        department          = i.department.name if  i.department else "N/A"
        designation         = i.designation.name if  i.designation else "N/A"
        negotiated_salary   = i.negotiated_salary
        interviewr_comments   = Truncator(i.interviewr_comments).chars(20)
        created_at          = i.created_at.strftime("%d-%b-%Y %I:%M %p").upper() if i.created_at else ""
        status              = i.status.title if i.status else "N/A"
        created_by          = '<a href="#aboutModal" data-toggle="modal" data-id="' + str(i.created_by_id) + '" class="user_info text-info" data-target="#userModal">' + i.created_by.name + '</a>' if i.created_by else 'N/A'
        action              = ""
        # edit_url        = reverse('hr:mp_budget_edit', kwargs={'id': i.id})
        action          += '<a href="#" class="h4 m-r-10 text-success view_recruitment" data-id='+str(i.id)+' title="View Recruitment"><i class="ti-eye"></i></a>'

        if i.created_by_id == int(request.session.get('id')) and (i.status!=Status.name('Approved') and i.status !=Status.name('authorized')):
            action          += '<a href="#" class="h4 m-r-10 text-success edit_recruitment" data-id='+str(i.id)+' title="Edit Recruitment"><i class="ti-pencil-alt"></i></a>'
        # action          = ebs_bl_common.action_html(action_url=edit_url, color_text='text-success', icon='ti-pencil-alt', title_text='Edit order')
        data = [recruit_year, company, department,designation,negotiated_salary,interviewr_comments,status,created_by,created_at, action]
        data_list.append(data)
    return JsonResponse(data_list, safe=False)
