from hr.views import *

@login
def leave_allocation_list(request):
    search_roles, company_query = {"Admin", "Management"}, Q(status=True)
    if not search_roles.intersection(request.session.get("user_roles")):
        company_query &= Q(id__in=request.session.get("company_id_list"))
    context = {
        'company_list'      : Company.objects.filter(company_query).order_by('short_name'),
        'department_list'   : Departments.objects.filter(status=True).order_by('short_name', 'name'),
        'designation_list'  : Designations.objects.filter(status=True).order_by('name'),
        'leave_type_list'   : HRLeaveType.objects.filter(status=True).order_by('short_title'),
        'employee_category_list':CommonMaster.objects.filter(value_for=5, status=True),
    }
    return render(request, 'hr/leave/allocation/list.html', context)

@csrf_exempt
def get_leave_allocation_for_datatable(request):
    start, counter = request.POST.get('start', 0), request.POST.get('counter', 0)
    query, reset_data, end = Q(), False, int(start) + int(counter)

    if company     := request.POST.get('company', None)     : query &= Q(employee__company_id=company)
    else :
        search_roles = {"Admin", "Management"}
        if not search_roles.intersection(request.session.get("user_roles")):
            query &= Q(employee__company_id__in=request.session.get("company_id_list"))
    if department  := request.POST.get('department', None)  : query &= Q(employee__department_id=department)
    if designation := request.POST.get('designation', None) : query &= Q(employee__designation_id=designation)
    if leave_type  := request.POST.get('leave_type', None)  : query &= Q(leave__leave_type_id=leave_type)
    if employee_category := request.POST.get('employee_category', None) : query &= Q(employee__employee_category_id=employee_category)

    if search_text := request.POST.get('search', None) :
        search_text = search_text.strip()
        query   &= Q(Q(employee__personal__employee_id__icontains=search_text)|Q(employee__personal__first_name__icontains=search_text)|Q(employee__personal__last_name__icontains=search_text))
    leave_list = HRLeaveAllocation.objects.filter(query).order_by("-id")
    total_data, content = leave_list.count(), ""
    if total_data == 0  : content, reset_data = "<tr><td class='font-weight-bold' colspan='10'>No Data Found!</td></tr>", True
    else :
        for i in leave_list[int(start):int(end)]:
            employee_id     = i.employee.personal.employee_id
            name            = i.employee.personal.name
            company         = i.employee.company.short_name if i.employee.company else "N/A"
            department      = i.employee.department.title if i.employee.department else "N/A"
            designation     = i.employee.designation.name if i.employee.designation else "N/A"
            fiscal_year     = i.fiscal_year.name
            leave_type      = i.leave.leave_type.short_title
            allocated_days  = i.allocated_days
            availed_days    = i.availed_days
            applied_days    = i.applied_days
            data = [employee_id, name, company, department, designation, fiscal_year, leave_type, allocated_days, availed_days, applied_days, '']
            content += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
    
    if 'true' == request.POST.get('reset', 'false') : reset_data = True
    end_pagination = False if int(end) < int(total_data) else True
    return JsonResponse({ "content":content, "end_pagination":end_pagination, "reset_data":reset_data, "total_data":total_data})

@login
def leave_allocation_company_wise(request):
    if request.method == "POST":
        company = request.POST.get("company", None)
        leaves  = request.POST.getlist("leave", [])
        ecs     = request.POST.getlist("employee_category", [])
        for leave in leaves:
            for ec in ecs:
                checked = request.POST.get("checkbox[{}][{}]".format(leave, ec), 0)
                allocated_days = request.POST.get("leave_days[{}][{}]".format(leave, ec), 0)
                if checked and allocated_days :
                    data = {
                        'company' : company, 'leave_type' : leave, 'employee_category' : ec,
                        'allocated_days' : allocated_days, 'status' : Status.name('Active'),
                        'created_by' : request.session.get('id'), 
                    }
                    form = HRLeaveMasterForm(data)
                    if form.is_valid() : form.save()
                    else : ebs_bl_common.form_errors(request, form)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    template_name   = "hr/leave/allocation/company.html"
    companies       = Company.objects.filter(status=True).order_by('short_name')
    employee_categories = CommonMaster.objects.filter(value_for=5)
    leave_types     = HRLeaveType.objects.filter(status=Status.name('Active'))
    context         = {'leave_types':leave_types, 'companies':companies, 'employee_categories':employee_categories}
    return render(request, template_name, context)


@login
def leave_allocation_user_wise(request):
    if request.method == "POST":
        leave_masters   = request.POST.getlist("leave_masters", [])
        users           = request.POST.getlist("users", [])
        added, updated, not_updated, failed = 0, 0, 0, 0
        current_fiscal_year = FiscalYear.objects.filter(status=Status.name('active')).order_by('-id').first()
        for leave in leave_masters:
            for user in users:
                checked = request.POST.get("checkbox[{}][{}]".format(user, leave), 0)
                allocated_days = request.POST.get("leave_days[{}][{}]".format(user, leave), 0)
                if checked and allocated_days :
                    allocation = HRLeaveAllocation.objects.filter(employee=user, leave=leave, fiscal_year=current_fiscal_year).last()
                    if allocation and allocation.availed_days == 0 and allocation.applied_days == 0 :
                        allocation.allocated_days = allocated_days
                        allocation.status = Status.name('Active')
                        allocation.updated_by = request.session.get('id')
                        allocation.save()
                        updated += 1
                    elif not allocation :
                        data = {
                            'opening_balance': 0, 'availed_days': 0, 'applied_days': 0,  'adjust_days': 0,  
                            'employee'  : user, 'leave' : leave, 'allocated_days' : allocated_days,
                            'status'    : Status.name('Active'), 'created_by' : request.session.get('id'),
                        }
                        form = HRLeaveAllocationForm(data)
                        if form.is_valid() : 
                            form.save()
                            added += 1
                        else : 
                            ebs_bl_common.form_errors(request, form)
                            failed += 1
                    else : not_updated += 1
        messages.success(request, "Added {} allocation/s, Updated {} allocation/s, Not Updated {} allocation/s, Failed {} allocation/s!".
            format(added, updated, not_updated, failed))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    user = get_object_or_404(Users, pk=request.session.get("id"))
    template_name   = "hr/leave/allocation/user.html"
    employee        = EmployeeDetails.objects.filter(personal__employee_id=user.employee_id).last()
    leave_types     = HRLeaveMaster.objects.filter(company_id=user.company_id, employee_category_id=employee.employee_category_id)
    users           = EmployeeDetails.objects.filter(personal__employee_id=user.employee_id)
    context         = {'leave_types':leave_types, 'users':users}
    return render(request, template_name, context)