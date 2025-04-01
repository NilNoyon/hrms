from hr.views import *


def leave_master_context(action_name='', instance=None):
    object_list         = HRLeaveMaster.objects.order_by('-id')
    employee_types      = CommonMaster.objects.filter(value_for=37)
    employee_categories = CommonMaster.objects.filter(value_for=38)
    companies           = Company.objects.filter(status=True).order_by("short_name")
    leave_types         = HRLeaveType.objects.filter(status=Status.name('Active'))
    if instance :
        action_url      = reverse_lazy('hr:leave_master_update', kwargs={'id':instance.id})
        form            = HRLeaveMasterForm(instance=instance)
    else :
        action_url      = reverse_lazy('hr:leave_master_list')
        form            = HRLeaveMasterForm()
    return { 'action_name':action_name, 'form':form, 'action_url':action_url, 'leave_types':leave_types, 'companies':companies, 
                'instance':instance, 'employee_types':employee_types, 'employee_categories':employee_categories, 'object_list' : object_list}

@login
def leave_master_list(request):
    # chk_permission = permission(request, reverse('hr:leave_master_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        leave = HRLeaveMaster.objects.filter(company=request.POST['company'], leave_type=request.POST['leave_type'],
                    employee_category=request.POST['employee_category'], employee_type=request.POST['employee_type'])
        if leave.exists() :
            messages.warning(request, "Already exists!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        request.POST['created_by'], status = request.session.get('id'), request.POST.get('status', None)
        request.POST['status'] = Status.name('Active' if status and status == 'on' else 'Inactive')
        form = HRLeaveMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/leave/master.html"
    context         = leave_master_context('Add Leave Master Data')
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def leave_master_update(request, id):
    # chk_permission = permission(request, reverse('hr:leave_master_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(HRLeaveMaster, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            leave = HRLeaveMaster.objects.exclude(id=id).filter(company=request.POST['company'], leave_type=request.POST['leave_type'], 
                        employee_category=request.POST['employee_category'], employee_type=request.POST['employee_type'])
            if leave.exists() :
                messages.warning(request, "Already exists!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            request.POST['updated_by'], status = request.session.get('id'), request.POST.get('status', None)
            request.POST['status'] = Status.name('Active' if status and status == 'on' else 'Inactive')
            form = HRLeaveMasterForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/leave/master.html"
        context         = leave_master_context("Update Leave Master Data", instance)
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:leave_master_list'))
    # else: return redirect(reverse("access_denied"))


@login
def leave_master_delete(request, id):
    instance = get_object_or_404(HRLeaveMaster, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))
    
@csrf_exempt
def leave_master_update_status(request):
    instance = get_object_or_404(HRLeaveMaster, id=request.POST.get('id'))
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return HttpResponse(instance.status)

@login
def import_leaves(request):
    if request.method == "POST":
        leave_list, user = [], get_object_or_404(Users, pk=request.session.get('id', None))
        import_file = request.FILES['import_file']
        info = pd.read_excel(import_file, 'Sheet1', engine='openpyxl')
        from inventory.view.views_item import retrun_str_from_xls as str_from_xls
        from hr.view.leave_application import generate_app_no
        for i in range(0, len(info)):
            employee_id = str_from_xls(info['Employee'][i])
            employee_dtl= EmployeeDetails.objects.filter(personal__employee_id=employee_id).last()
            leave_type_str= str_from_xls(info['Leave Type'][i])
            leave_type  = HRLeaveType.objects.filter(short_title=leave_type_str).last()
            num_of_days = str_from_xls(info['Num of Days'][i])
            start_date  = str_from_xls(info['Start date'][i], date_field = True)
            end_date    = str_from_xls(info['End date'][i], date_field = True)
            avail_place = str_from_xls(info['Avail place'][i])
            reason      = str_from_xls(info['Reason'][i])
            is_post_approved = True if str_from_xls(info['Is post approved'][i]).title() == "Yes" else False
            rp_boss_id  = str_from_xls(info['Reporting boss'][i])
            rp_boss     = Users.objects.filter(employee_id=rp_boss_id).last()
            reporting_boss_notes = str_from_xls(info['Reporting boss notes'][i])
            dept_head_id = str_from_xls(info['Dept Head'][i])
            dept_head   = Users.objects.filter(employee_id=dept_head_id).last()
            dept_head_notes = str_from_xls(info['Dept Head notes'][i])
            hr_id  = str_from_xls(info['HR'][i])
            hr     = Users.objects.filter(employee_id=hr_id).last()
            hr_notes = str_from_xls(info['HR notes'][i])
            if employee_dtl and leave_type and start_date and end_date :
                if not num_of_days :
                    delta = end_date - start_date
                    num_of_days = delta.days + 1
                allocated_leave = HRLeaveAllocation.objects.filter(employee=employee_dtl, leave__leave_type_id=leave_type).last()
                if not allocated_leave or int(allocated_leave.total_balance) < int(num_of_days) : continue
                elif HRLeaveApplication.objects.filter(employee=employee_dtl, start_date=start_date, end_date=end_date).last() : continue
                if hr and hr.id                 : status = Status.name('Approved')
                elif dept_head and dept_head.id : status = Status.name('Recommended')
                elif rp_boss and rp_boss.id     : status = Status.name('Forwarded')
                else                            : status = Status.name('Raised')
                data = {'application_no' : generate_app_no(employee_dtl.company), 'employee' : employee_dtl, 'leave' : leave_type, 'start_date' : start_date, 'end_date' : end_date, 'avail_place' : avail_place, 'reason' : reason, 'created_by' : user, 'reporting_boss' : rp_boss, 'reporting_boss_notes' : reporting_boss_notes, 'reporting_boss_checked_at' : datetime.now(), 'dept_head' : dept_head, 'dept_head_notes' : dept_head_notes, 'dept_head_checked_at' : datetime.now(), 'hr' : hr, 'hr_notes' : hr_notes, 'hr_checked_at' : datetime.now(), 'is_post_approved' : is_post_approved, 'status' : status}
                form = HRLeaveApplicationForm(data)
                if form.is_valid() : 
                    application = form.save()
                    allocation = application.allocation()
                    if status == Status.name('Approved') : 
                            allocation.availed_days += application.num_of_days
                    else :  allocation.applied_days += application.num_of_days
                    allocation.save()
                    leave_list.append(application)
                else : ebs_bl_common.form_error_print(request, form)
        messages.success(request, "You have successfully imported {} leave/s information.".format(len(set(leave_list))))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return render(request, 'hr/leave/import.html')

def import_leave_balance(request):
    if request.method == "POST":
        from inventory.view.views_item import retrun_str_from_xls as str_from_xls
        leave_list, user = [], get_object_or_404(Users, pk=request.session.get('id', None))
        import_file = request.FILES['import_file']
        xl          = pd.ExcelFile(import_file, engine='openpyxl')
        current_fiscal_year = FiscalYear.objects.filter(status=Status.name('active')).order_by('-id').first()
        for sheet in xl.sheet_names:
            if sheet == "Leave Policy"      :
                info = pd.read_excel(import_file, sheet, engine='openpyxl', dtype={'Employee ID':str})
                for i in range(0, len(info)):
                    if company := Company.objects.filter(short_name__iexact=str_from_xls(info['Company'][i], change_quote=False)).first() :
                        if leave_type_str  := str_from_xls(info['Leave Type (Short Name)'][i]) :
                            if leave_type_obj      := HRLeaveType.objects.filter(short_title=leave_type_str).first() : leave_type = leave_type_obj
                            else : leave_type       = HRLeaveType.objects.create(short_title=leave_type_str, description=leave_type_str, status=Status.name('Active'), created_by=user)
                        if employee_type_text      := str_from_xls(info['Employment Type'][i]) :
                            if employee_type_obj   := CommonMaster.objects.filter(value_for=37, value=employee_type_text).first() : employee_type = employee_type_obj
                            else : employee_type    = CommonMaster.objects.create(value_for=37, value=employee_type_text)
                        if employee_category_text  := str_from_xls(info['Employee Category'][i]) :
                            if employee_category_obj:= CommonMaster.objects.filter(value_for=38, value=employee_category_text).first() : employee_category = employee_category_obj
                            else : employee_category = CommonMaster.objects.create(value_for=38, value=employee_category_text)
                        allocated_days  = str_from_xls(int(float(info['Allocated Days'][i] if str(info['Allocated Days'][i]) != 'nan' else 0)))
                        if leave_policy := HRLeaveMaster.objects.filter(company=company, leave_type=leave_type, 
                            employee_type=employee_type, employee_category=employee_category).first() :
                            leave_policy.allocated_days = allocated_days
                            leave_policy.save()
                        else : HRLeaveMaster.objects.create(company=company, leave_type=leave_type, employee_type=employee_type, 
                            employee_category=employee_category, allocated_days=allocated_days, status=Status.name('active'), created_by=user)
            elif sheet == "Leave Balance" :
                info = pd.read_excel(import_file, sheet, engine='openpyxl', dtype={'Employee ID':str})
                for i in range(0, len(info)):
                    employee_id     = str_from_xls(info['Employee ID'][i])
                    if employee_dtl:= EmployeeDetails.objects.filter(personal__employee_id=employee_id).last():
                        leave_type_str  = str_from_xls(info['Leave Type (Short Name)'][i])
                        leave           = HRLeaveMaster.objects.filter(company=employee_dtl.company,employee_type=employee_dtl.employee_type, employee_category=employee_dtl.employee_category, leave_type__short_title=leave_type_str).last()
                        opening_balance = str_from_xls(int(float(info['Opening Balance'][i] if str(info['Opening Balance'][i]) != 'nan' else 0)))
                        allocated_days  = str_from_xls(int(float(info['Allocated Days'][i] if str(info['Allocated Days'][i]) != 'nan' else 0)))
                        if not allocated_days or allocated_days == '0' : 
                            allocated_days = leave.allocated_days if leave else 0
                        availed_days    = str_from_xls(int(float(info['Availed Days'][i] if str(info['Availed Days'][i]) != 'nan' else 0)))
                        applied_days    = str_from_xls(int(float(info['Applied Days'][i] if str(info['Applied Days'][i]) != 'nan' else 0)))
                        adjust_days     = str_from_xls(int(float(info['Adjust Days'][i] if str(info['Adjust Days'][i]) != 'nan' else 0)))
                        data = {
                            'employee'          : employee_dtl, 
                            'leave'             : leave, 
                            'fiscal_year'       : current_fiscal_year,
                            'opening_balance'   : opening_balance, 
                            'allocated_days'    : allocated_days,
                            'availed_days'      : availed_days, 
                            'applied_days'      : applied_days,
                            'adjust_days'       : adjust_days,
                            'created_by'        : user,
                            'created_at'        : datetime.now(),
                            'status'            : Status.name('Active'),
                        }
                        if allocation := HRLeaveAllocation.objects.filter(employee=employee_dtl, leave=leave, fiscal_year=current_fiscal_year).first() :
                            data['updated_by'] = user
                            data['updated_at'] = datetime.now()
                            if not allocation.created_by : data['created_by'] = user
                            else : data['created_by'] = allocation.created_by
                            if not allocation.created_at : data['created_at'] = datetime.now()
                            else : data['created_at'] = allocation.created_at
                            form = HRLeaveAllocationForm(data, instance=allocation)
                        else : form = HRLeaveAllocationForm(data)
                        if form.is_valid() : 
                            allocation = form.save()
                            leave_list.append(allocation)
                        else : ebs_bl_common.form_error_print(request, form)
        messages.success(request, "You have successfully imported {} leave/s information.".format(len(set(leave_list))))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return render(request, 'hr/leave/import_balance.html')