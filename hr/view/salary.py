from hr.views import *
from weasyprint import HTML
from django.template.loader import get_template
from calendar import monthrange, month_name
from general.templatetags.data_load import is_role_assigned
# from hr.tasks import process_salary

month_list = {
    '1' : 'January',
    '2' : 'February',
    '3' : 'March',
    '4' : 'April',
    '5' : 'May',
    '6' : 'June',
    '7' : 'July',
    '8' : 'August',
    '9' : 'September',
    '10' : 'October',
    '11' : 'November',
    '12' : 'December',
}
bn_month_list = {
    '1' : 'জানুয়ারি',
    '2' : 'ফেব্রুয়ারী',
    '3' : 'মার্চ',
    '4' : 'এপ্রিল',
    '5' : 'মে',
    '6' : 'জুন',
    '7' : 'জুলাই',
    '8' : 'আগষ্ট',
    '9' : 'সেপ্টেম্বর',
    '10' : 'অক্টোবর',
    '11' : 'নভেম্বর',
    '12' : 'ডিসেম্বর',
}

@login
def salary_process2(request):
    chk_permission = permission(request, reverse('hr:salary_process2'))
    if request.session.get('employee_id', '') in ['NGO00001001'] or chk_permission and chk_permission.insert_action:
        if request.method == "POST":
            ids, month, year = [], request.POST.get('month', None), request.POST.get('year', None)
            for emp_id in request.POST.getlist('emp_id', []):
                if not HRSalaryProcess.objects.filter(employees__id=emp_id, month=month, year=year).exists():
                    ids.append(emp_id)
            if len(ids) > 0 :
                data = {
                    'employees' : ids, 'month' : month, 'year' : year,
                    'notes'     : request.POST.get('notes', None),
                    'created_by': get_object_or_404(Users, pk=request.session.get("id", "")),
                    'status'    : Status.name("Started")
                }
                form = HRSalaryProcessForm(data)
                if form.is_valid():
                    sp = form.save()
                    process_salary_func(sp.id)
                    messages.success(request, "Process Started!")
                else : ebs_bl_common.form_errors(request, form)
            else : messages.warning(request, "No Employee Found for Salary Process!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        year_list, month_list, current_month, current_year = [], HRMontlySalaryDetails.month_list, datetime.now().month, datetime.now().year
        if current_month == 1 : year_list, month_list = [current_year - 1, current_year], [month_list[10], month_list[11], month_list[0]]
        elif current_month == 2 : year_list, month_list = [current_year - 1, current_year], [month_list[11], month_list[0], month_list[1]]
        else : year_list, month_list = [current_year], [month_list[current_month-3], month_list[current_month-2], month_list[current_month-1]]
        
        context = { 
            'years' : year_list, 'months' : month_list, 
            'companies'     : Branch.objects.filter(status = True, company_id=request.session.get('company_id')).order_by('name'),
            'categories'    : CommonMaster.objects.filter(value_for=5, status = True),
            'departments'   : Departments.objects.filter(status = True).order_by('name'), 
            'shifts'        : Shift.objects.filter(status=Status.name('active')) 
        }
        return render(request, "hr/salary/process.html", context)
    else: return redirect('/access-denied')

def process_salary_func(sp_id=None):
    salary_process = get_object_or_404(HRSalaryProcess, pk=sp_id)
    num_of_days, per_day_amount, basic, user = 30, 0, 0, salary_process.created_by
    for employee in salary_process.employees.all():
        if salary_cycle := HRSalaryCycle.objects.filter(branch=employee.branch, employee_category=employee.employee_category).first() :
            if salary_cycle.start_date != 1 : 
                syear = year = int(salary_process.year)
                month = int(salary_process.month)
                if month == 1:
                    month = 13
                    syear -= 1
                start_date  = datetime(syear, month-1, salary_cycle.start_date, 0, 0, 0)
                end_date    = datetime(year, month, salary_cycle.end_date, 0, 0, 0)
                attendance_query    = Q(calendar_day__gte=start_date, calendar_day__lte=end_date)
            else: attendance_query  = Q(calendar_day__month=salary_process.month, calendar_day__year=salary_process.year)
            calendar_days   = EmployeeCalendar.objects.filter(attendance_query & Q(employee=employee))
            absent_days     = calendar_days.filter(absent=True).count()
            absent_days    += calendar_days.filter(in_leave=True, leave_application__leave__payable=False).count()
            for s in HRSalaryBreakdown.objects.filter(employee=employee) :
                amount = s.amount
                if s.slab_heads.head.value == 'Basic' :
                    per_day_amount, basic = round(s.amount / num_of_days, 0), amount
                    # if absent_days != 0 : amount = round(per_day_amount * ( num_of_days - absent_days ), 0)
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, slab_head=s.slab_heads, user=user)
            
            # Absent Payment
            if absent_days and per_day_amount :
                absent_days = absent_days if absent_days < num_of_days else num_of_days
                amount = round(per_day_amount * absent_days, 0)
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, head_name="Absent", head_type="DV", user=user)
            
            # Holiday Payment
            if holidays := EmployeeCalendar.objects.filter(Q(Q(is_holiday=True)|Q(is_weekend=True)), Q(employee=employee, employee__holiday_bonus=True, calendar_day__month=salary_process.month, calendar_day__year=salary_process.year), Q(attendance__isnull=False)).count() :
                amount = round(per_day_amount * holidays * 2, 0)
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, head_name="Holiday", head_type="AV", user=user)
            
            # OT Payment
            ot_hours_obj = EmployeeCalendar.objects.filter(employee=employee, employee__overtime=True, 
                calendar_day__month=salary_process.month, calendar_day__year=salary_process.year).annotate(total_ot=Sum('attendance__ot_hours'))
            if ot_hours_obj.count() :
                ot_hours = sum(o.total_ot for o in ot_hours_obj if o.total_ot)
                amount = round((basic / 206) * ot_hours * 2, 0) # 208 = 26 days * 8 hours per day
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, head_name="Over Time", head_type="AV", user=user)

            # Loan Deduction
            if employee.loans.filter(closed=False).count() > 0 :
                loan_amount = 0
                for loan_val in employee.loans.filter(closed=False):
                    loan_amount += int(loan_val.monthly_installment)
                    LoanRepayment.objects.create(loan=loan_val, amount_paid=loan_val.monthly_installment, payment_date=datetime.now().date(), remarks="Paid from the Salary of " + salary_process.get_month_display() + " " + salary_process.year)
                    loan_val.amount_paid += int(loan_val.monthly_installment)
                    loan_val.save()
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=loan_amount, employee=employee, head_name='Loan', head_type="DV", user=user)
                
    salary_process.status = Status.name('completed')
    salary_process.save()


@csrf_exempt
def get_salary_process_for_datatable(request):
    start, counter = request.POST.get('start', 0), request.POST.get('counter', 0)
    query, content, reset_data, end = Q(), '', False, int(start) + int(counter)
    user = get_object_or_404(Users, pk=request.session.get("id", 0))
    user_level = user.sc_user_level()
    if status_text := request.POST.get('status', None) :
        if status_text == 'pending' :
            chk_permission = permission(request, reverse('hr:salary_process2'))
            if request.session.get('employee_id', '') in ['NGO00001001'] or chk_permission and chk_permission.insert_action:
                query &= Q(status__in=[Status.name('started'), Status.name('rejected')])
            elif is_role_assigned(str(request.session.get('user_roles', '')).lower(), 'cfo'):
                query &= Q(status=Status.name('checked'))
            elif is_role_assigned(str(request.session.get('user_roles', '')).lower(), 'finance'):
                query &= Q(status=Status.name('approved'))
            elif user_level == 3 :
                query &= Q(status=Status.name('recommended'))
            elif request.session.get("is_head", 0) :
                query &= Q(status=Status.name('submitted'))
        elif status_text == 'list' :
            # if is_role_assigned(str(request.session.get('user_roles', '')).lower(), 'payroll officer'):
            chk_permission = permission(request, reverse('hr:salary_process2'))
            if request.session.get('employee_id', '') in ['NGO00001001'] or chk_permission and chk_permission.insert_action:
                query &= ~Q(status__in=[Status.name('started'), Status.name('rejected')])
            elif is_role_assigned(str(request.session.get('user_roles', '')).lower(), 'cfo'):
                query &= Q(status__in=[Status.name('approved'), Status.name('acknowledged')])
            elif is_role_assigned(str(request.session.get('user_roles', '')).lower(), 'finance'):
                query &= Q(status=Status.name('acknowledged'))
            elif user_level == 3 :
                query &= ~Q(status__in=[Status.name('started'), Status.name('rejected'), Status.name('submitted'), Status.name('recommended')])
            elif request.session.get("is_head", 0) :
                query &= ~Q(status__in=[Status.name('started'), Status.name('rejected'), Status.name('submitted')])

            
    
    query_data_list = HRSalaryProcess.objects.filter(query).order_by('-created_at')
    total_data, content = query_data_list.count(), ""
    if total_data == 0  : 
        content, reset_data = "<tr><td class='font-weight-bold text-center text-danger' colspan='7'>No Data Found!</td></tr>", True
    else :  
        for r in query_data_list[int(start):int(start)+20] :
            created_by  = ebs_bl_common.user_html(r.created_by, 25)
            created_at  = ebs_bl_common.date_time_format(r.created_at)
            created_at  = ebs_bl_common.datatable_center_td(created_at)
            # edit_url    = reverse('hr:roaster_update', kwargs={'id': r.id})
            # edit        = '<a class="h4 m-r-10 text-success edit_btn" href="javascript:void(0);" data-id="' + str(r.id)
            # edit       += '" data-url="' + edit_url + '" ><span class="icon"><i class="ti-pencil-alt"></i></span></a>'
            view_url, delete = reverse('hr:salary_process_view', kwargs={'id': r.id}), ''
            view        = ebs_bl_common.action_html(action_url=view_url, color_text='text-info m-r-10', icon='icon-eye', title_text='View Employee')
            if r.status in [Status.name('Started'), Status.name('Completed'), Status.name('Submitted')] and user == r.created_by : 
                delete_url  = reverse('hr:salary_process_delete', kwargs={'id': r.id})
                delete      = '<a class="h4 text-danger delete_btn" href="javascript:void(0);" data-url="'
                delete     += delete_url + '"><span class="icon"><i class="ti-trash"></i></span></a>'
            action      = ebs_bl_common.datatable_center_td(view + delete)
            data = [r.year, month_list[r.month], str(r.employees.count()), r.status.title, created_by, created_at, action]
            content += "<tr>" + "".join("<td>{}</td>".format(str(d)) for d in data) + "</tr>"
    
    if 'true' == request.POST.get('reset', 'false') : reset_data = True
    end_pagination = False if int(end) < int(total_data) else True
    return JsonResponse({ "content":content, "end_pagination":end_pagination, "reset_data":reset_data, "total_data":total_data})

@csrf_exempt
def salary_process_delete(request, id):
    instance = get_object_or_404(HRSalaryProcess, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login
def salary_process_view(request, id=None):
    salary_process = HRSalaryProcess.objects.get(id=id)
    user = n_sender = get_object_or_404(Users, pk=request.session.get("id", 0))
    user_level = user.sc_user_level()
    if request.method == "POST":
        status, rejected = request.POST.get('status', None), request.POST.get('rejected', None)
        notes = request.POST.get('notes', None) if rejected == '0' else request.POST.get('reject_notes', None)
        if status == 'submitted':
            salary_process.submitted_at         = datetime.now()
            salary_process.notes                = notes
            n_recipient                         = Users.objects.filter(Q(is_department_head=True),
                Q(Q(role__name__icontains='hr')|Q(role__name__icontains='human')|Q(secondary_role__contains=['hr', 'human'])))
        elif status == 'recommended':
            salary_process.recommend_by         = user
            salary_process.recommend_reject_date= datetime.now()
            salary_process.recommend_notes      = notes
            n_recipient                         = Users.objects.filter(role__name='Audit')
        elif status == 'checked':
            salary_process.check_by             = user
            salary_process.check_reject_date    = datetime.now()
            salary_process.check_notes          = notes
            n_recipient                         = Users.objects.filter(Q(role__name__icontains='cfo')|Q(secondary_role__contains=['cfo']))
        elif status == 'approved':
            salary_process.approve_by           = user
            salary_process.approve_reject_date  = datetime.now()
            salary_process.approve_notes        = notes
            n_recipient                         = Users.objects.filter(Q(role__name__icontains='finance')|Q(secondary_role__contains=['finance']))
        elif status == 'acknowledged':
            salary_process.acknowledge_by       = user
            salary_process.acknowledge_reject_date = datetime.now()
            salary_process.acknowledge_notes    = notes
            n_recipient                         = salary_process.created_by

        if rejected == '1' : 
            status      = 'rejected'
            n_recipient = salary_process.created_by
        salary_process.status = Status.name(status)
        salary_process.save()
        messages.success(request, "Successfully {}!".format(status.capitalize()))

        # Send Notification
        n_model         = 'HRSalaryProcess'
        n_verb          = 'Salary ' + status.capitalize()
        n_description   = "1 new Salary Process of your is " + status + " in Supply Chain"
        n_is_repeated   = True
        n_action_url    = reverse('hr:salary_process')
        notify.send(n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model, verb=n_verb, description=n_description, is_repeated=n_is_repeated)

        return redirect(request.META.get('HTTP_REFERER', '/'))


    template_name   = "hr/salary/process_view.html"
    emp_data, month = [], int(salary_process.month)
    syear = year = int(salary_process.year)
    for employee in salary_process.employees.order_by('employee_id'):
        basic       = get_salary_breakdown(employee=employee, heads='Basic')
        hrent       = get_salary_breakdown(employee=employee, heads='House Rent')
        medical     = get_salary_breakdown(employee=employee, heads='Medical Allowance')
        conveyance  = get_salary_breakdown(employee=employee, heads='Conveyance')
        food        = get_salary_breakdown(employee=employee, heads='Food Allowance')
        other       = get_salary_breakdown(employee=employee, heads='Other Allowance')

        present, absent_days, with_pay, without_pay, working_day, total_days, holiday_n_weekends = 0, 0, 0, 0, 0, 0, 0
        if salary_cycle := HRSalaryCycle.objects.filter(branch=employee.branch, employee_category=employee.employee_category).first() :
            weekend_query = Q(holiday__branch=employee.branch)
            if salary_cycle.start_date != 1 : 
                if month == 1:
                    month = 13
                    syear -= 1
                start_date      = date(syear, month-1, salary_cycle.start_date)
                end_date        = date(year, month, salary_cycle.end_date)
                total_days      = (end_date - start_date).days + 1
                weekend_query  &= Q(holiday_date__gte=start_date, holiday_date__lte=end_date)
                attendance_query= Q(calendar_day__gte=start_date, calendar_day__lte=end_date)
            else : 
                total_days      = monthrange(int(year), int(month))[1]
                weekend_query  &= Q(holiday_date__month=month, holiday_date__year=year)
                attendance_query= Q(calendar_day__month=month, calendar_day__year=year)
            calendar_days       = EmployeeCalendar.objects.filter(attendance_query & Q(employee=employee))
            status_counts       = calendar_days.aggregate(present_count=Count('id', filter=Q(attendance__isnull=False)), absent_count=Count('id', filter=Q(absent=True)), weekend_count=Count('id', filter=Q(is_weekend=True)), holiday_count=Count('id', filter=Q(is_holiday=True)))
            present, absent_days= status_counts['present_count'], status_counts['absent_count']
            holiday_n_weekends  = status_counts['weekend_count'] + status_counts['holiday_count']
            without_pay         = calendar_days.filter(in_leave=True, leave_application__leave__payable=False).count()
            with_pay            = calendar_days.filter(in_leave=True, leave_application__leave__payable=True).count()
        
        # Addition
        holiday     = get_salary_details(year=year, month=month, employee=employee, heads='Holiday')
        ot          = get_salary_details(year=year, month=month, employee=employee, heads='Over Time')
        night       = get_salary_details(year=year, month=month, employee=employee, heads='Night')
        attendance  = get_salary_details(year=year, month=month, employee=employee, heads='Attendance')
        incentive   = get_salary_details(year=year, month=month, employee=employee, heads='Incentive')
        # festival    = get_salary_details(year=year, month=month, employee=employee, heads='Festival')
        arrear      = get_salary_details(year=year, month=month, employee=employee, heads='Arrear')
        tiffin      = get_salary_details(year=year, month=month, employee=employee, heads='Tifin Bill')

        #Deduction
        loan    = get_salary_details(year=year, month=month, employee=employee, heads='Loan')
        absent  = get_salary_details(year=year, month=month, employee=employee, heads='Absent')
        others  = get_salary_details(year=year, month=month, employee=employee, heads='Others')
        itds    = get_salary_details(year=year, month=month, employee=employee, heads='ITDS')
        pf      = get_salary_details(year=year, month=month, employee=employee, heads='PF')

        deduction_days = absent_days - without_pay
        working_day, salary_days = total_days - holiday_n_weekends, 30 - deduction_days
        salary_payable  = employee.salary # - Decimal(deduction_days).quantize(Decimal('0.00')) * Decimal(employee.salary / 30).quantize(Decimal('0.00'))
        total_payable   = salary_payable + ot + holiday + night + attendance + incentive + arrear + tiffin # + festival
        net_payable     = total_payable - loan - absent - others - itds - pf
        # for salary in HRMontlySalaryDetails.objects.filter(year=year, month=month, employee=employee) :
        per_hr_amount   = round(basic / 206, 2) if basic else 0

        data = { "employee_id":employee.employee_id, "name":employee.name, "company":employee.branch.short_name, "department":employee.department.title, "designation":employee.designation.name, "cost_center":employee.cost_center.short_name if employee.cost_center else '', "grade":employee.grade, "employee_category":employee.employee_category.value if employee.employee_category_id else "N/A", "joining_date":employee.joining_date.strftime("%d/%m/%Y") if employee.joining_date else '', "salary":employee.salary, "basic":basic, "hrent":hrent, "medical":medical, "conveyance":conveyance, "food":food, "other":other, "working_day":working_day, "holiday_n_weekends":holiday_n_weekends, "total_days":total_days, "present":present, "absent_days":absent_days, "with_pay":with_pay, "without_pay":without_pay, "ot_hrs":round(ot / (per_hr_amount * 2), 0) if ot else 0, "salary_payable":round(salary_payable, 0), "ot":ot, "holiday":holiday, "night":night, "attendance":attendance, "incentive":incentive, "arrear":arrear, "tiffin":tiffin, "total_payable":round(total_payable, 0), "loan":loan, "absent":absent, "others":others, "itds":itds, "pf":pf, "net_payable":round(net_payable, 0)}
        print(data)
        emp_data.append(data)
    context = {'salary_process':salary_process, 'month':month_list[salary_process.month], 'emp_data':emp_data, 'user_level':user_level}
    return render(request, template_name, context)

@csrf_exempt
def get_employee_data_for_salary_process(request):
    report_data, query = '', Q(status=Status.name('Active'))
    if company     := request.POST.get('company', None)     : query &= Q(branch_id=company)
    if department  := request.POST.get('department', None)  : query &= Q(department_id=department)
    if designation := request.POST.get('designation', None) : query &= Q(designation_id=designation)
    if category_list := request.POST.getlist('category[]', None): query &= Q(employee_category_id__in=category_list)
    if employee_list := request.POST.getlist('employee[]', [])  : query &= Q(id__in=employee_list)
    for employee in EmployeeDetails.objects.filter(query).order_by('employee_id') :
        company     = employee.branch.short_name if employee.branch else ''
        department  = employee.department.title if employee.department_id else ''
        designation = employee.designation.title if employee.designation_id else ''
        employee_id = employee.personal.employee_id if employee.personal_id else ''
        name        = employee.personal.name if employee.personal_id else ''
        category    = employee.employee_category.value if employee.employee_category_id else ''
        data = [company, department, designation, employee_id, name, category, employee.salary]
        report_data += "<tr><td><div class='custom-control custom-checkbox mb-1'>"
        report_data += "<input type='checkbox' class='custom-control-input check_emp'"
        report_data += "name='emp_id' value='" + str(employee.id) + "' id='check-[" + str(employee.id) + "]'>"
        report_data += "<label class='custom-control-label' for='check-[" + str(employee.id) + "]'></label></div></td>"
        report_data += "".join("<td>{}</td>".format(d) for d in data) + "</tr>"
    return JsonResponse({"report_data":report_data}, safe=False)

@login
def salary_process(request):
    chk_permission   = permission(request, reverse('hr:salary_process'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            company             = Branch.objects.filter(id=request.POST.get("company", None)).first()
            department          = Departments.objects.filter(id=request.POST.get("department", None)).first()
            employee_category   = CommonMaster.objects.filter(id=request.POST.get("employee_category", None)).first()
            user                = get_object_or_404(Users, pk=request.session.get("id"))
            month, year         = int(request.POST.get("month", None)), int(request.POST.get("year", None))
            num_of_days, per_day_amount, basic = 30, 0, 0
            # num_of_days, per_day_amount, basic = monthrange(year, month)[1], 0, 0

            for employee in EmployeeDetails.objects.filter(personal__employee_id='LE01000074', branch=company, department=department, employee_category=employee_category):
                if salary_cycle := HRSalaryCycle.objects.filter(branch=employee.branch, employee_category=employee.employee_category).first() :
                    if salary_cycle.start_date != 1 : 
                        syear = year
                        if month == 1:
                            month = 13
                            syear -= 1
                        start_date          = datetime(syear, month-1, salary_cycle.start_date, 0, 0, 0)
                        end_date            = datetime(year, month, salary_cycle.end_date, 0, 0, 0)
                        attendance_query    = Q(calendar_day__gte=start_date, calendar_day__lte=end_date)
                    else: attendance_query  = Q(calendar_day__month=month, calendar_day__year=year)
                    calendar_days   = EmployeeCalendar.objects.filter(attendance_query & Q(employee=employee))
                    absent_days     = calendar_days.filter(absent=True).count()
                    absent_days    += calendar_days.filter(in_leave=True, leave_application__leave__payable=False).count()
                    for s in HRSalaryBreakdown.objects.filter(employee=employee) :
                        amount = s.amount
                        if s.slab_heads.heads == 'Basic' :
                            per_day_amount, basic = round(s.amount / num_of_days, 0), amount
                            if absent_days != 0 : amount = round(per_day_amount * ( num_of_days - absent_days ), 0)
                        salary_details_entry(year=year, month=month, amount=amount, employee=employee, slab_head=s.slab_heads, user=user)
                    
                    # Absent Payment
                    if absent_days and per_day_amount :
                        amount = round(per_day_amount * absent_days, 0)
                        salary_details_entry(year=year, month=month, amount=amount, employee=employee, head_name="Absent", head_type="DV", user=user)
                    
                    # Holiday Payment
                    if holidays := EmployeeCalendar.objects.filter(Q(Q(is_holiday=True)|Q(is_weekend=True)), 
                                    Q(employee=employee, employee__holiday_bonus=True, 
                                      calendar_day__month=month, calendar_day__year=year)).count() :
                        amount = round(per_day_amount * holidays * 2, 0)
                        salary_details_entry(year=year, month=month, amount=amount, employee=employee, head_name="Holiday", head_type="AV", user=user)
                    
                    # OT Payment
                    ot_hours_obj = EmployeeCalendar.objects.filter(employee=employee, employee__overtime=True, 
                        calendar_day__month=month, calendar_day__year=year).annotate(total_ot=Sum('attendance__ot_hours'))
                    if ot_hours_obj.count() :
                        ot_hours = sum(o.total_ot for o in ot_hours_obj if o.total_ot)
                        amount = round((basic / 206) * ot_hours * 2, 0) # 208 = 26 days * 8 hours per day
                        salary_details_entry(year=year, month=month, amount=amount, employee=employee, head_name="Over Time", head_type="AV", user=user)
                    
            messages.success(request, "Salary Processed for {} {} of {} category, {} department and {}!".format(
                month_name[month], year, employee_category.value, department.title, company.short_name))                   
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
        year_list, month_list, current_month, current_year = [], HRMontlySalaryDetails.month_list, datetime.now().month, datetime.now().year
        if current_month == 1 : year_list, month_list = [current_year - 1, current_year], [month_list[10], month_list[11], month_list[0]]
        elif current_month == 2 : year_list, month_list = [current_year - 1, current_year], [month_list[11], month_list[0], month_list[1]]
        else : year_list, month_list = [current_year], [month_list[current_month-3], month_list[current_month-2], month_list[current_month-1]]
        companies = Company.objects.filter(status = True).order_by('name')
        employee_categories = CommonMaster.objects.filter(value_for=5)
        department_list = Departments.objects.filter(status=True)
        context = {'years' : year_list, 'months' : month_list, 'companies' : companies,
                   'employee_categories' : employee_categories, 'departments' : department_list }
        return render(request, 'hr/salary/salary_process.html', context)
    else: return redirect('/access-denied')

def salary_details_entry(year=None, month=None, amount=0, employee=None, slab_head=None, head_name="", head_type="AV", user=None):
    if not slab_head : 
        salary_head, created = CommonMaster.objects.get_or_create(value=head_name, value_for=9, status=True)
        slab_head, created = HRSalarySlabMaster.objects.get_or_create(head=salary_head, type=head_type, 
            slab=employee.employee_category, created_by=user, status=Status.name('Active'))
    if salary_details := HRMontlySalaryDetails.objects.filter(year=year, month=month, employee=employee, heads=slab_head).first() :
        salary_details.amount = amount
        salary_details.save()
    else : HRMontlySalaryDetails.objects.create(year=year, month=month, amount=amount, employee=employee, heads=slab_head)

@login
def salary_report(request):
    # chk_permission   = permission(request, reverse('hr:salary_process'))
    # if chk_permission and chk_permission.view_action:
    chk_permission = permission(request, reverse('hr:salary_process2'))
    if request.session.get('employee_id', '') in ['NGO00001001'] or chk_permission and chk_permission.insert_action:
        year_list, month_list, current_month, current_year = [], HRMontlySalaryDetails.month_list, datetime.now().month, datetime.now().year
        if current_month == 1 : year_list, month_list = [current_year - 1, current_year], [month_list[10], month_list[11], month_list[0]]
        elif current_month == 2 : year_list, month_list = [current_year - 1, current_year], [month_list[11], month_list[0], month_list[1]]
        else : year_list, month_list = [current_year], [month_list[current_month-3], month_list[current_month-2], month_list[current_month-1]]
        companies = Branch.objects.filter(status = True, company_id=request.session.get('company_id')).order_by('name')
        employee_categories = CommonMaster.objects.filter(value_for=5)
        department_list = Departments.objects.filter(status=True)
        context = {'years' : year_list, 'months' : month_list, 'companies' : companies,
                   'employee_categories' : employee_categories, 'departments' : department_list }
        return render(request, 'hr/salary/report.html', context)
    else: return redirect('/access-denied')

# @login
# def festival_bonus(request):
#     companies = Company.objects.filter(status = True).order_by('name')
#     employee_categories = CommonMaster.objects.filter(value_for=5)
#     department_list = Departments.objects.filter(status=True)
#     context = {'companies' : companies, 'employee_categories' : employee_categories, 'departments' : department_list }
#     return render(request, 'hr/salary/festival.html', context)

# @csrf_exempt
# def get_festival_report(request):
#     report_data, cut_of_date, query = "", request.POST.get("date", ""), Q(status=Status.name("Active"))
#     cut_of_date = datetime.strptime(cut_of_date, "%Y-%m-%d").date() if cut_of_date else ''
#     if company := request.POST.get('company', None) : 
#         query &= Q(company_id=company)
#         company = Company.objects.filter(id=company).first()
#     if department := request.POST.get('department', None)   : query &= Q(department_id=department)
#     if employee_category := request.POST.get('employee_category', None) : query &= Q(employee_category_id=employee_category)
#     for employee in EmployeeDetails.objects.filter(query).order_by('personal__employee_id'):
#         bank_info = EmployeeBankInfo.objects.filter(employee=employee).first()
#         basic, bonus = get_salary_breakdown(employee=employee, heads='Basic'), 0
#         day_diff = cut_of_date - employee.joining_date.date()
#         if basic == 0 : continue
#         elif day_diff.days >= 365 : bonus = basic
#         else :
#             if employee.employee_category.value == 'Worker' : continue
#             elif 'Staff' in employee.employee_category.value :
#                 bonus = round(float(day_diff.days / 365) * float(basic), 0)
#                 if "Management" in employee.employee_category.value :
#                     bonus = bonus if bonus > 2000 else 2000
#                 else : bonus = bonus if bonus > 1000 else 1000
#         data = [employee.company.short_name, employee.department.title, employee.cost_center.short_name if employee.cost_center else '',
#                 employee.employee_category.value, employee.section.name if employee.section_id else '', employee.employee_id, employee.name, employee.designation.name,
#                 employee.joining_date.strftime("%d-%b-%y"), cut_of_date.strftime("%d-%b-%y"), day_diff.days, employee.salary, basic, bonus, bank_info.account_no]
#         report_data += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
#     return JsonResponse({"report_data":report_data}, safe=False)

def get_salary_breakdown(employee=None, heads=''):
    slab_head = HRSalaryBreakdown.objects.filter(employee=employee, slab_heads__head__value__iexact=heads).first()
    return round(slab_head.amount, 0) if slab_head else 0

def get_salary_details(year=None, month=None, employee=None, heads=''):
    detail = HRMontlySalaryDetails.objects.filter(year=year, month=month, employee=employee, heads__head__value__iexact=heads).last()
    return round(detail.amount, 0) if detail else 0

@csrf_exempt
def get_salary_report(request):
    from decimal import Decimal
    report_type, report_data, query  = request.POST.get('report_type', None), '', Q(status=Status.name("Active"))
    if company := request.POST.get('company', None)         : 
        query  &= Q(branch_id=company)
        company = Branch.objects.filter(id=company).first()
    if department := request.POST.get('department', None) : query &= Q(department_id=department)
    if employee_category := request.POST.get('employee_category', None) : query &= Q(employee_category_id=employee_category)
    month, year     = int(request.POST.get("month", None)), int(request.POST.get("year", None))
    for employee in EmployeeDetails.objects.filter(query).order_by('personal__employee_id'):
        basic       = get_salary_breakdown(employee=employee, heads='Basic')
        hrent       = get_salary_breakdown(employee=employee, heads='House Rent')
        medical     = get_salary_breakdown(employee=employee, heads='Medical Allowance')
        conveyance  = get_salary_breakdown(employee=employee, heads='Conveyance')
        food        = get_salary_breakdown(employee=employee, heads='Food Allowance')
        other       = get_salary_breakdown(employee=employee, heads='Other Allowance')

        late, absent_days, with_pay, without_pay, working_day, total_days, holiday_n_weekends = 0, 0, 0, 0, 0, 0, 0
        if salary_cycle := HRSalaryCycle.objects.filter(branch=employee.branch, employee_category=employee.employee_category).first() :
            weekend_query = Q(holiday__branch=company)
            if salary_cycle.start_date != 1 : 
                syear = year
                if month == 1:
                    month = 13
                    syear -= 1
                start_date      = date(syear, month-1, salary_cycle.start_date)
                end_date        = date(year, month, salary_cycle.end_date)
                total_days      = (end_date - start_date).days + 1
                weekend_query  &= Q(holiday_date__gte=start_date, holiday_date__lte=end_date)
                attendance_query= Q(calendar_day__gte=start_date, calendar_day__lte=end_date)
            else : 
                total_days      = monthrange(year, month)[1]
                weekend_query  &= Q(holiday_date__month=month, holiday_date__year=year)
                attendance_query= Q(calendar_day__month=month, calendar_day__year=year)
            holiday_n_weekends  = HolidayIndividuals.objects.filter(weekend_query).count()
            calendar_days       = EmployeeCalendar.objects.filter(attendance_query & Q(employee=employee))
            absent_days         = calendar_days.filter(absent=True).count()
            late                = calendar_days.filter(is_late=True).count()
            with_pay            = calendar_days.filter(in_leave=True, leave_application__leave__payable=True).count()
            without_pay         = calendar_days.filter(in_leave=True, leave_application__leave__payable=False).count()
        
        # Addition
        holiday     = get_salary_details(year=year, month=month, employee=employee, heads='Holiday')
        ot          = get_salary_details(year=year, month=month, employee=employee, heads='Over Time')
        night       = get_salary_details(year=year, month=month, employee=employee, heads='Night')
        attendance  = get_salary_details(year=year, month=month, employee=employee, heads='Attendance')
        incentive   = get_salary_details(year=year, month=month, employee=employee, heads='Incentive')
        # festival    = get_salary_details(year=year, month=month, employee=employee, heads='Festival')
        arrear      = get_salary_details(year=year, month=month, employee=employee, heads='Arrear')
        tiffin      = get_salary_details(year=year, month=month, employee=employee, heads='Tifin Bill')

        #Deduction
        loan    = get_salary_details(year=year, month=month, employee=employee, heads='Loan')
        absent  = get_salary_details(year=year, month=month, employee=employee, heads='Absent')
        others  = get_salary_details(year=year, month=month, employee=employee, heads='Others')
        itds    = get_salary_details(year=year, month=month, employee=employee, heads='ITDS')
        pf      = get_salary_details(year=year, month=month, employee=employee, heads='PF')

        deduction_days = absent_days - without_pay
        working_day, salary_days = total_days - holiday_n_weekends, 30 - deduction_days
        salary_payable  = employee.salary # - Decimal(deduction_days).quantize(Decimal('0.00')) * Decimal(employee.salary / 30).quantize(Decimal('0.00'))
        total_payable   = salary_payable + ot + holiday + night + attendance + incentive + arrear + tiffin # + festival
        net_payable     = total_payable - loan - absent - others - itds - pf
        # for salary in HRMontlySalaryDetails.objects.filter(year=year, month=month, employee=employee) :
        per_hr_amount   = round(basic / 206, 2) if basic else 0

        data = [employee.employee_id, employee.branch.code+' '+employee.branch.name, employee.department.title, employee.designation.name,
                employee.cost_center.short_name if employee.cost_center else '', employee.grade, employee.employee_category.value, 
                employee.joining_date.strftime("%d/%m/%Y"), employee.salary, basic, hrent, medical, conveyance,
                food, other, working_day, holiday_n_weekends, total_days, late, absent_days, with_pay, without_pay, 
                round(ot / (per_hr_amount * 2), 0) if ot else 0, round(salary_payable, 0), ot, holiday, night, attendance,
                incentive, arrear, tiffin, round(total_payable, 0), loan, absent, others, itds, pf, round(net_payable, 0)]
        report_data += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
    if report_type == "pdf" :
        template = get_template('hr/salary/report_pdf.html')
        html = template.render({'company':company, 'data':report_data, 'month':month_list[str(month)], 'year':year})
        pdf_file = HTML(string=html).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'Salary Report.pdf'
        return response
    return JsonResponse({"report_data":report_data}, safe=False)

@login
def pay_slip(request):
    if request.session.get('employee_id', ''):
        year_list, month_list, current_month, current_year = [], HRMontlySalaryDetails.month_list, datetime.now().month, datetime.now().year
        if current_month == 1 : year_list, month_list = [current_year - 1, current_year], [month_list[10], month_list[11], month_list[0]]
        elif current_month == 2 : year_list, month_list = [current_year - 1, current_year], [month_list[11], month_list[0], month_list[1]]
        else : year_list, month_list = [current_year], [month_list[current_month-3], month_list[current_month-2], month_list[current_month-1]]
        context = { 'years' : year_list, 'months' : month_list,
            'companies' : Branch.objects.filter(status = True, company_id=request.session.get('company_id')).order_by('name'),
            'departments' : Departments.objects.filter(status=True).order_by('name'),
            'designation_list'  : Designations.objects.filter(status = True).order_by('name'),
            'employee_categories' : CommonMaster.objects.filter(value_for=5).order_by('value')}
        return render(request, 'hr/salary/pay_slip.html', context)
    else: return redirect('/access-denied')

@csrf_exempt
def get_payslip_report(request):
    report_type, report_format, all_data = request.POST.get('report_type', None), request.POST.get('report_format', None), []
    report_data, query  = '', Q(status=Status.name("Active"))
    if company := request.POST.get('company', None)         : 
        query &= Q(branch_id=company)
        company = Branch.objects.filter(id=company).first()
    if department := request.POST.get('department', None)   : query &= Q(department_id=department)
    if employee_category := request.POST.get('employee_category', None) : query &= Q(employee_category_id=employee_category)
    if employees := request.POST.getlist('user', []) : query &= Q(id__in=employees)
    if employees := request.POST.getlist('user[]', []) : query &= Q(id__in=employees)
    month, year = int(request.POST.get("month", None)), int(request.POST.get("year", None))
    for employee in EmployeeDetails.objects.filter(query).order_by('personal__employee_id'):
        # Addition
        holiday     = get_salary_details(year=year, month=month, employee=employee, heads='Holiday')
        ot          = get_salary_details(year=year, month=month, employee=employee, heads='Over Time')
        night       = get_salary_details(year=year, month=month, employee=employee, heads='Night')
        attendance  = get_salary_details(year=year, month=month, employee=employee, heads='Attendance')
        incentive   = get_salary_details(year=year, month=month, employee=employee, heads='Incentive')
        festival    = get_salary_details(year=year, month=month, employee=employee, heads='Festival')
        arrear      = get_salary_details(year=year, month=month, employee=employee, heads='Arrear')
        tiffin      = get_salary_details(year=year, month=month, employee=employee, heads='Tifin Bill')

        #Deduction
        loan    = get_salary_details(year=year, month=month, employee=employee, heads='Loan')
        absent  = get_salary_details(year=year, month=month, employee=employee, heads='Absent')
        others  = get_salary_details(year=year, month=month, employee=employee, heads='Others')
        itds    = get_salary_details(year=year, month=month, employee=employee, heads='ITDS')
        pf      = get_salary_details(year=year, month=month, employee=employee, heads='PF')

        total_payable   = holiday + night + attendance + incentive + festival + arrear + tiffin
        total_deduction = loan + absent + others + itds + pf
        net_payable     = employee.salary + total_payable + ot - total_deduction

        if report_type == 'print': 
            basic       = get_salary_breakdown(employee=employee, heads='Basic')
            hrent       = get_salary_breakdown(employee=employee, heads='House Rent')
            medical     = get_salary_breakdown(employee=employee, heads='Medical Allowance')
            conveyance  = get_salary_breakdown(employee=employee, heads='Conveyance')
            food        = get_salary_breakdown(employee=employee, heads='Food Allowance')
            other       = get_salary_breakdown(employee=employee, heads='Other Allowance')

            late, absent_days, with_pay, without_pay, working_day, total_days, weekends, holidays = 0, 0, 0, 0, 0, 0, 0, 0
            if salary_cycle := HRSalaryCycle.objects.filter(branch=employee.branch, employee_category=employee.employee_category).first() :
                weekend_query = Q(holiday__company=company)
                if salary_cycle.start_date != 1 : 
                    syear = year
                    if month == 1:
                        month = 13
                        syear -= 1
                    start_date      = date(year, month-1, salary_cycle.start_date)
                    end_date        = date(year, month, salary_cycle.end_date)
                    total_days      = (end_date - start_date).days + 1
                    weekend_query  &= Q(holiday_date__gte=start_date, holiday_date__lte=end_date)
                    attendance_query= Q(calendar_day__gte=start_date, calendar_day__lte=end_date)
                else : 
                    total_days      = monthrange(year, month)[1]
                    weekend_query  &= Q(holiday_date__month=month, holiday_date__year=year)
                    attendance_query= Q(calendar_day__month=month, calendar_day__year=year)
                holidays_data       = HolidayIndividuals.objects.filter(weekend_query & Q(holiday__weekend=False))
                holidays            = holidays_data.count()
                weekends            = HolidayIndividuals.objects.filter(weekend_query & Q(holiday__weekend=True)
                                        ).exclude(holiday_date__in=holidays_data.values_list('holiday_date', flat=True)).count()
                calendar_days       = EmployeeCalendar.objects.filter(attendance_query & Q(employee=employee))
                present_days        = calendar_days.filter(attendance__isnull=False).count()
                absent_days         = calendar_days.filter(absent=True).count()
                late                = calendar_days.filter(is_late=True).count()
                with_pay            = calendar_days.filter(in_leave=True, leave_application__leave__payable=True).count()
                without_pay         = calendar_days.filter(in_leave=True, leave_application__leave__payable=False).count()

                ot_rate             = (round(basic / 206, 2) if basic else 0) * 2
                data = {'employee':employee, 'basic':basic, 'hrent':hrent, 'medical':medical, 'conveyance':conveyance, 'food':food,
                    'other':other, 'working_day':total_days - holidays - weekends, 'weekends':weekends, 'holidays':holidays, 'total_days':total_days, 
                    'late':late, 'present_days':present_days, 'absent_days':absent_days, 'with_pay':with_pay, 'without_pay':without_pay, 'holiday':holiday, 
                    'ot_rate':ot_rate if ot else 0, 'ot_hrs':round(ot / ot_rate, 0) if ot else 0, 'ot':ot, 'night':night, 'attendance':attendance, 
                    'incentive':incentive, 'festival':festival, 'arrear':arrear, 'tiffin':tiffin, 'total_payable':round(total_payable, 0), 
                    'loan':loan, 'absent':absent, 'others':others, 'itds':itds, 'pf':pf, 'total_deduction':round(total_deduction, 0), 'net_payable':round(net_payable, 0)}
                data['joining_month'] = bn_month_list[str(int(employee.joining_date.strftime("%m")))]
                all_data.append(data)
        else : 
            data = [employee.employee_id, employee.branch.short_name, employee.department.title, employee.designation.name,
            employee.employee_category.value, round(employee.salary, 0), round(total_payable, 0), round(total_deduction, 0), 
            round(net_payable, 0)]
            report_data += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
            
    if report_type == 'print'       : 
        if report_format == "EN"    :
            context = {'company':company, 'data':all_data, 'month':month_list[str(month)], 'year':year}
            return render(request, 'hr/salary/pay_slip_print.html', context)
        elif report_format == "BN"  :
            context = {'company':company, 'data':all_data, 'month':bn_month_list[str(month)], 'year':year}
            return render(request, 'hr/salary/pay_slip_print_bn.html', context)
    return JsonResponse({"report_data":report_data}, safe=False)
