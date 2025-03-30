from hr.views import *
from hr.models import HolidayIndividuals


@login
def holiday_list(request):
    # chk_permission = permission(request, reverse('hr:holiday_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        user        = get_object_or_404(Users, pk=request.session.get("id"))
        company     = request.POST.get('company', None)
        setup_list  = request.POST.getlist('setup', [])
        for setup in setup_list:
            status = Status.name('Active' if request.POST.get('status[{}]'.format(setup), None) == 'on' else 'Inactive')
            duration = request.POST.get('duration[{}]'.format(setup), None)
            if duration:
                durations = duration.split(" - ")
                start_date= datetime.strptime(durations[0], "%d/%m/%Y") if durations[0] else ''
                if len(durations) != 1 :
                    end_date  = datetime.strptime(durations[1], "%d/%m/%Y") if durations[1] else ''
                else : end_date = start_date
            else : start_date, end_date = None, None
            data = {
                'setup' : setup, 'start_date' : start_date, 'end_date' : end_date,
                'company' : company, 'status' : status, 'created_by' : user,
                'name'  : request.POST.get('name[{}]'.format(setup), None),
               
            }
            holiday = request.POST.get('holiday[{}]'.format(setup), None)
            if holiday :
                instance= get_object_or_404(Holiday, id=holiday)
                data['created_by'] = instance.created_by
                data['updated_by'] = user
                form    = HolidayForm(data, instance=instance)
            else : form = HolidayForm(data)
            if form.is_valid()  : form.save()
            else : ebs_bl_common.form_errors(request, form)
        if company := Company.objects.filter(id=company).first() :
            if has_weekend := HolidaySetup.objects.filter(name="Weekend").first(): 
                has_weekend.status  = Status.name("active")
                has_weekend.fixed   = False
                has_weekend.updated_by = user
                has_weekend.save()
            else : has_weekend = HolidaySetup.objects.create(name="Weekend", status=Status.name("active"), fixed=False, created_by=user)
            if holiday := Holiday.objects.filter(company=company, setup=has_weekend, name="Weekend").first():
                holiday.status      = Status.name("active")
                holiday.weekend     = True
                holiday.updated_by  = user
                holiday.save()
            else : holiday = Holiday.objects.create(company=company, setup=has_weekend, created_by=user, name="Weekend", weekend=True, status=Status.name("active"))
            ystart = date(datetime.now().year, 1, 1)  # Get the first day of the current year
            yend = date(datetime.now().year, 12, 31)  # Get the last day of the current year
            delta, weekends = timedelta(days=1), []
            HolidayIndividuals.objects.filter(holiday_date__year=datetime.now().year,holiday=holiday).delete()
            if company.weekends :
                for w in company.weekends:
                    weekends += [d for d in (ystart + (n * delta) for n in range((yend - ystart).days + 1)) if d.weekday() == int(w)]
                for w in weekends:
                    if hexist := HolidayIndividuals.objects.filter(holiday=holiday, holiday_date=w).first() : 
                        hexist.status       = Status.name("active")
                        hexist.updated_by   = user
                        hexist.save()
                    else : hexist = HolidayIndividuals.objects.create(holiday=holiday, holiday_date=w, created_by=user, status=Status.name("active"))
            
        messages.success(request, "Successfully Stored!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    template_name   = "hr/holiday/base.html"
    return render(request, template_name, holiday_context())
    # else: return redirect(reverse("access_denied"))

@login
def holiday_calendar(request):
    template_name   = "hr/holiday/calendar.html"
    context = {
        'company_list'  : Branch.objects.filter(status=True, company_id=request.session.get('company_id')).order_by('name'),
        'user_company'  : Branch.objects.filter(id=request.session.get('branch_id')).first()
    }
    return render(request, template_name, context)

@csrf_exempt
def get_calendar_data(request):
    company_id, holidays, html = request.POST.get('company_id', None), [], ''
    holiday_list = Holiday.objects.filter(start_date__year=datetime.now().year,
                     branch_id=company_id, status=Status.name("active")).order_by('start_date')
    holiday_indivs_list = HolidayIndividuals.objects.filter(holiday_date__year=datetime.now().year,
                     holiday__branch_id=company_id, status=Status.name("active")).order_by('holiday_date')
    holidays.append({ 'name' : "Today", 
        'startYear' : datetime.today().strftime("%Y"), 'startMonth' : datetime.today().strftime("%m"), 
        'startDay' : datetime.today().strftime("%d"), 'endYear' : datetime.today().strftime("%Y"), 
        'endMonth' : datetime.today().strftime("%m"), 'endDay' : datetime.today().strftime("%d") })
    for hi in holiday_indivs_list:
        data = { 'name' : hi.holiday.name, 
                'startYear' : hi.holiday_date.strftime("%Y"), 'startMonth' : hi.holiday_date.strftime("%m"), 
                'startDay' : hi.holiday_date.strftime("%d"), 'endYear' : hi.holiday_date.strftime("%Y"), 
                'endMonth' : hi.holiday_date.strftime("%m"), 'endDay' : hi.holiday_date.strftime("%d") }
        holidays.append(data)
    for h in holiday_list:
        if h.start_date == h.end_date : hdate = h.start_date.strftime("%d-%b-%Y").upper()
        else : hdate = h.start_date.strftime("%d-%b-%Y").upper() + """ - """ + h.end_date.strftime("%d-%b-%Y").upper()
        html += """ <tr>
                <td>""" + h.name + """</td>
                <td class='text-center'>""" + hdate + """</td>
                </tr> """
    return JsonResponse({'data' : holidays, 'html' : html}, safe=False)


@csrf_exempt
def company_weekends(request):
    if request.method == "POST":
        user        = get_object_or_404(Users, pk=request.session.get("id"))
        weekend_list= request.POST.getlist('weekend', [])
        for w in HolidayIndividuals.objects.filter(id__in=weekend_list):
            if holidate := request.POST.get('date[{}]'.format(w.id), None) :
                w.holiday_date = datetime.strptime(holidate, "%d/%m/%Y")
                w.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
    context = { 'company_list' : Branch.objects.filter(status=True, company_id=request.session.get('company_id')).order_by('name') }
    return render(request, "hr/holiday/weekend.html", context)


@csrf_exempt
def get_weekend_data(request):
    company_id, html = request.POST.get('company_id', None), ''
    weekend_list = HolidayIndividuals.objects.filter(holiday_date__year=datetime.now().year, holiday__weekend=True,
                    holiday__branch_id=company_id, status=Status.name("active")).order_by('holiday_date')
    for index, w in enumerate(weekend_list):
        html += """<div class="col-md-3">
                    <div class="input-group">
                        <div class="input-group-append">
                            <button class="btn btn-light" type="button" style="width:120px;">Weekend """ + str(index+1) + """</button>
                        </div>
                        <div class="form-group">
                            <input type="hidden" name="weekend" value='""" + str(w.id) + """' />
                            <input type="text" class="form-control bg-transparent singledate text-right" name="date[""" + str(w.id) + """]" 
                                value='""" + w.holiday_date.strftime('%d/%m/%Y') + """'  autocomplete="off">
                            <span class="bar"></span>
                        </div>
                    </div>
                </div>"""
    if weekend_list.count() :
        html += """<div class="col-md-3 ml-auto">
                        <button type="submit" id="submit_btn" class="mt-2 btn btn-sm btn-block waves-effect waves-light btn-rounded btn-success">
                            <span class="btn-label"><i class="fa fa-check"></i></span> Submit
                        </button>
                </div>"""
    return JsonResponse({'html' : html}, safe=False)