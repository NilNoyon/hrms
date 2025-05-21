from hr.views import *


@login
def holiday_setup_list(request):
    # chk_permission = permission(request, reverse('hr:holiday_setup_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        date    = request.POST.get('date', None)
        month   = request.POST.get('month', None)
        name, query = request.POST.get('name', None), Q()
        fixed   = request.POST.get('fixed', 0)
        
        if (date and not month) or (not date and month) \
            or (not date and not month and fixed) :
            messages.warning(request, "Date and Month both required for Fixed Holiday!")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if date and month : query = Q(date=date, month=month)
        elif name : query = Q(name__iexact=name)
        setup   = HolidaySetup.objects.filter(query).last()
        if setup:
            messages.warning(request, "With this information Holiday setup already exist!")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        request.POST = request.POST.copy()
        request.POST['created_by'] = request.session.get('id')
        status = request.POST.get('status', None)
        request.POST['status'] = Status.name('Active' if status and status == 'on' else 'Inactive')
        request.POST['fixed'] = 1 if fixed and fixed == 'on' else 0
        form = HolidaySetupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/holiday/base.html"
    context         = holiday_context()
    context['tab_name'] = 'holiday_setup'
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))

@login
def holiday_setup_update(request, id):
    instance = get_object_or_404(HolidaySetup, id=id)
    if request.method == "POST":
        date    = request.POST.get('date', None)
        month   = request.POST.get('month', None)
        name, query = request.POST.get('name', None), Q()
        fixed   = request.POST.get('fixed', 0)
        
        if (date and not month) or (not date and month) \
            or (not date and not month and fixed) :
            messages.warning(request, "Date and Month both required for Fixed Holiday!")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if date and month : query = Q(date=date, month=month)
        elif name : query = Q(name__iexact=name)
        setup   = HolidaySetup.objects.filter(query).exclude(id=id).last()
        if setup:
            messages.warning(request, "With this information Holiday setup already exist!")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        request.POST = request.POST.copy()
        request.POST['updated_by'] = request.session.get('id')
        status = request.POST.get('status', None)
        request.POST['status'] = Status.name('Active' if status and status == 'on' else 'Inactive')
        request.POST['fixed'] = 1 if fixed and fixed == 'on' else 0
        form = HolidaySetupForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Updated!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/holiday/base.html"
    context         = holiday_context()
    context['tab_name'] = 'holiday_setup'
    context['saction_name'] = "Update Entry"
    context['saction_url']  = reverse_lazy('hr:holiday_setup_update', kwargs={'id':id})
    context['sform']        = HolidaySetupForm(instance=instance)
    context['sinstance']    = instance
    return render(request, template_name, context) 

@login
def holiday_setup_delete(request, id):
    instance = get_object_or_404(HolidaySetup, id=id)
    if instance.holiday.count() == 0 :
        instance.delete()
        messages.success(request, "Successfully Deleted!")
    else : messages.warning(request, "Already in list, can't be deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def get_holiday_company_data(request):
    yearly_setups, year, company_id = [], datetime.now().year, request.POST.getlist('company_id', None)
    for setup in HolidaySetup.objects.filter(status=Status.name("active")).exclude(name="Weekend").order_by('month', 'date'):
        current_data    = Holiday.objects.filter(start_date__year=year, setup=setup, branch__in=company_id).first()
        if current_data:
            holiday_id  = current_data.id
            status      = current_data.status
            start_date  = current_data.start_date
            end_date    = current_data.end_date
            num_of_days = (current_data.end_date - current_data.start_date).days + 1
        else :
            status, holiday_id = Status.name("Active"), None
            if setup.fixed :
                start_date = end_date = datetime.strptime(str(setup.date) + "/" + str(setup.month) + "/" + str(year), '%d/%m/%Y')
                num_of_days = 1
            else : start_date, end_date, num_of_days = None, None, None
        data = {
            'holiday_id': holiday_id,
            'setup_id'  : setup.id,
            'title'     : setup.name,
            'start_date': start_date, 
            'end_date'  : end_date,
            'status'    : status,
            'fixed'     : setup.fixed,
            'num_of_days':num_of_days
        }
        yearly_setups.append(data)
    context = {'yearly_setups':yearly_setups}
    return render(request, 'hr/holiday/update.html', context)

@csrf_exempt
def holiday_setup_update_fixed_status(request):
    instance = get_object_or_404(HolidaySetup, id=request.POST.get('id'))
    stype = request.POST.get('stype')

    message = ""
    if stype == 'fixed':
        instance.fixed = 1 if instance.fixed == 0 else 0
        message = "Fixed status updated"
    else:
        instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
        message = "Holiday status updated"

    instance.save()

    return JsonResponse({
        "success": True,
        "message": message,
        "fixed": instance.fixed,
        "status": str(instance.status),  # Convert to string here
    })