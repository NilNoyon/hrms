from hr.views import *


@login
def attendance_list(request):
    template_name   = "hr/attendance/list.html"
    context         = {
        'company_list'      : Branch.objects.filter(company_id=request.session.get('company_id')).order_by('short_name'),
        'designation_list'  : Designations.objects.filter(status = True).order_by('name'),
        'department_list'   : Departments.objects.filter(status = True).order_by('name'),
        'user_list'         : Users.objects.filter(status = True),
        'attendances'       : Attendance.objects.order_by('-id')[0:20],
    }
    return render(request, template_name, context)

@login
def attendance_entry(request):
    logged_user = get_object_or_404(Users, pk=request.session.get("id"))
    if request.method == "POST":
        users = request.POST.getlist("users", [])
        date_field = request.POST.get('attendance_date', '')
        attend_date = datetime.strptime(date_field, "%d-%b-%Y").date() if date_field else ''
        for user in users:
            it_field = (request.POST.get("in_time[{}]".format(user), 0)).split(":")
            in_time = time(int(it_field[0]), int(it_field[1]), int(it_field[2])) if it_field[2] else None
            ot_field = (request.POST.get("out_time[{}]".format(user), 0)).split(":")
            out_time = time(int(ot_field[0]), int(ot_field[1]), int(ot_field[2])) if ot_field[2] else None
            outside_office = request.POST.get("outside_office[{}]".format(user), 0)
            data = {
                'employee' : user, 'present_day' : attend_date,
                'shift'    : request.POST.get("shift[{}]".format(user), 0),
                'location' : request.POST.get("location[{}]".format(user), 0),
                'in_time'  : in_time, 'out_time' : out_time, 
                'outside_office' : 1 if outside_office else 0,
                'created_by' : logged_user, 'status' : Status.name("active"),
            }
            form = AttendanceForm(data)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/attendance/entry.html"
    context         = {
        'company_list'      : Company.objects.filter(status = True).order_by('name'),
        'designation_list'  : Designations.objects.filter(status = True).order_by('name'),
        'department_list'   : Departments.objects.filter(status = True).order_by('name'),
        'user_list'         : Users.objects.filter(status = True),
        'users'             : EmployeeDetails.objects.filter(personal__employee_id=logged_user.employee_id),
        'shifts'            : Shift.objects.filter(status = Status.name("Active")),
        'locations'         : Location.objects.filter(status = Status.name("Active")),
    }
    return render(request, template_name, context)

@login
def attendance_report(request):
    from calendar import monthrange, weekday
    template_name, attendances = "hr/attendance/report.html", []
    attendance_list = Attendance.objects.filter(employee__personal__employee_id="EC00007234", present_day__month=datetime.now().month, present_day__year=datetime.now().year).order_by('present_day')
    for a in attendance_list:
        output = [idx for idx, attendance in enumerate(attendances) if attendance['employee_id'] == a.employee.personal.employee_id]
        if output : pass
        else :
            data = {'employee_id':a.employee.personal.employee_id, 'personal':a.employee.personal, 'present' : 0, 'absent' : 0, 'leave' : 0, 'holiday' : 0, 'late' : 0, 'date_data' : []}
            attendances.append(data)

    context = {
        'company_list'      : Company.objects.filter(status = True).order_by('name'),
        'designation_list'  : Designations.objects.filter(status = True).order_by('name'),
        'department_list'   : Departments.objects.filter(status = True).order_by('name'),
        'num_of_days'       : monthrange(datetime.now().year, datetime.now().month)[1],
        'attendances'       : attendances
    }
    return render(request, template_name, context)

@csrf_exempt
def get_monthly_report_data(request):
    template_name, query = "hr/attendance/monthly_report_data.html", Q(status=Status.name('active'))
    if employee := request.POST.get('employee', None) : query &= Q(id=employee)
    else :
        if company := request.POST.get('company', None)         : query &= Q(company_id=company)
        if department := request.POST.get('department', None)   : query &= Q(department_id=department)
        if designation := request.POST.get('designation', None) : query &= Q(designation_id=designation)
    attendance_date = request.POST.get('attendance_date', None)
    year, month     = date.today().year, date.today().month
    if attendance_date : 
        dates       = attendance_date.split("-")
        start_date  = datetime.strptime(dates[0], "%d/%m/%Y")
        end_date    = datetime.strptime(dates[1], "%d/%m/%Y")
    else : 
        start_date      = datetime(year, month, 1)
        if month != 12 : end_date = datetime(year, int(month) + 1, 1) - timedelta(days=1)
        else : end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    range_days, data = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)], []
    for employee in EmployeeDetails.objects.filter(query).order_by('personal__employee_id'):
        log_data = []
        for rdate in range_days :
            log = EmployeeCalendar.objects.filter(calendar_day=rdate, employee=employee).first()
            remarks = ""
            if rdate.date() > date.today() : remarks = ""
            elif log : remarks = log.day_status
            log_data.append(remarks)
        status_counts = EmployeeCalendar.objects.filter(employee=employee, calendar_day__range=(start_date, end_date)).aggregate( present_count=Count('id', filter=Q(attendance__isnull=False)), absent_count=Count('id', filter=Q(absent=True)), weekend_count=Count('id', filter=Q(is_weekend=True)), leave_count=Count('id', filter=Q(leave_application__isnull=False)))
        emp_data = { 'employee' : employee, 'range_days': log_data, 'total' : len(log_data), 'weekends' : status_counts['weekend_count'], 'leave' : status_counts['leave_count'],  'present' : status_counts['present_count'], 'absent' : status_counts['absent_count'] }
        data.append(emp_data)
    context = {'dates':range_days, 'data':data, 'start_date':start_date.strftime('%d-%m-%Y'), 'end_date':end_date.strftime('%d-%m-%Y')}
    return render(request, template_name, context)


@login
def job_card(request):
    template_name = "hr/attendance/job_card.html"
    context = {
        'company_list'      : Company.objects.filter(status = True).order_by('name'),
        'designation_list'  : Designations.objects.filter(status = True).order_by('name'),
        'department_list'   : Departments.objects.filter(status = True).order_by('name'),
    }
    return render(request, template_name, context)

@csrf_exempt
def get_job_card_data(request):
    report_data, query, date_query = '', Q(status=Status.name("Active")), Q()
    if employee := request.POST.get('employee', None) : query &= Q(id=employee)
    else :
        if company := request.POST.get('company', None)         : query &= Q(company_id=company)
        if department := request.POST.get('department', None)   : query &= Q(department_id=department)
        if designation := request.POST.get('designation', None) : query &= Q(designation_id=designation)
    attendance_date = request.POST.get('attendance_date', None)
    if attendance_date  :
        dates       = attendance_date.split("-")
        start_date  = datetime.strptime(dates[0], "%d/%m/%Y")
        end_date    = datetime.strptime(dates[1], "%d/%m/%Y") + timedelta(days=1)
        date_query &= Q(calendar_day__gte=start_date, calendar_day__lt=end_date)
    for employee in EmployeeDetails.objects.filter(query).order_by('personal__employee_id'):
        calendar_log = EmployeeCalendar.objects.filter(date_query & Q(employee=employee))
    return JsonResponse({"report_data":report_data}, safe=False)
 

@login
def my_job_card(request, employee_id="", start_date="", end_date=""):
    template_name, date_query = "hr/attendance/my_job_card.html", Q()
    if not employee_id : employee_id = request.session.get("employee_id", None)
    employee        = EmployeeDetails.objects.filter(employee_id=employee_id).first()
    if start_date   : start_date    = datetime.strptime(start_date, "%d-%m-%Y")
    if end_date     : end_date      = datetime.strptime(end_date, "%d-%m-%Y")
    if not (start_date and end_date) :
        year, month     = date.today().year, date.today().month 
        start_date      = datetime(year, month, 1)
        if month != 12 :
            end_date    = datetime(year, int(month) + 1, 1) - timedelta(days=1)
        else : end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        if salary_cycle:= HRSalaryCycle.objects.filter(branch=employee.branch, employee_category=employee.employee_category).first() :
            if salary_cycle.start_date != 1 : 
                start_date  = datetime(year, month - 1, salary_cycle.start_date)
                end_date    = datetime(year, month, salary_cycle.end_date)
    
    range_days, calendar_logs = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)], []
    weekends, holidays, present = 0, 0, 0
    for rdate in range_days :
        if employee.holiday and str(rdate.weekday()) in employee.holiday : weekends += 1
        log = EmployeeCalendar.objects.filter(calendar_day=rdate, employee=employee).first()
        data = {"log_date" : rdate, "shift" : employee.shift.name if employee.shift else "", "shift_start"  : employee.shift.start_time.strftime("%I:%M %p") if employee.shift and employee.shift.start_time else "", "shift_end" : employee.shift.end_time.strftime("%I:%M %p") if employee.shift and employee.shift.end_time else "", "late_time" : "00:00", "early_leave_time" : "00:00", "remarks" : ""}
        if log : data['remarks'] = log.day_remarks
        if rdate.date() > date.today() :
            data['in_time'] = data['out_time'] = data['late_time'] = data['early_leave_time'] = ""
            data['remarks'] = ""
        elif log and log.attendance :
            present += 1
            data['in_time']     = log.attendance.in_time.strftime("%I:%M %p") if log.attendance.in_time else ""
            data['out_time']    = log.attendance.out_time.strftime("%I:%M %p") if log.attendance.out_time else ""
            data['work_hrs']    = log.attendance.work_hours
            data['late_time']   = log.attendance.late_time
            data['early_leave_time']= log.attendance.early_leave_time
            if log.attendance.shift :
                data['shift']       = log.attendance.shift.name
                data['shift_start'] = log.attendance.shift.start_time.strftime("%I:%M %p") if log.attendance.shift.start_time else ""
                data['shift_end']   = log.attendance.shift.end_time.strftime("%I:%M %p") if log.attendance.shift.end_time else ""
            if str(rdate.weekday()) in employee.holiday : data['remarks'] = "Weekend"
        elif rdate.date() < date.today() :
            data['in_time'] = data['out_time'] = data['late_time'] = data['early_leave_time'] = data['work_hrs'] = "00:00:00"
            if employee.holiday and str(rdate.weekday()) in employee.holiday : data['remarks']  = "Weekend"
        calendar_logs.append(data)
    status_counts = EmployeeCalendar.objects.filter(calendar_day__range=(start_date, end_date), employee=employee).aggregate( present_count=Count('id', filter=Q(attendance__isnull=False)), absent_count=Count('id', filter=Q(absent=True)), weekend_count=Count('id', filter=Q(is_weekend=True)), leave_count=Count('id', filter=Q(leave_application__isnull=False)))
    context = { 'employee':employee, 'calendar_logs':calendar_logs, 'total_days':len(calendar_logs), 'weekends' : status_counts['weekend_count'], 'leave' : status_counts['leave_count'],  'present' : status_counts['present_count'], 'absent' : status_counts['absent_count']}
    return render(request, template_name, context)   


@login
def daily_attendance_report(request):
    template_name = "hr/attendance/daily-report.html"
    context = {
        'company_list'      : Company.objects.filter(status = True).order_by('name'),
        'designation_list'  : Designations.objects.filter(status = True).order_by('name'),
        'department_list'   : Departments.objects.filter(status = True).order_by('name'),
    }
    return render(request, template_name, context)

@csrf_exempt
def get_daily_attendance_report_data(request):
    report_data, query, date_query = '', Q(status=Status.name("Active")), Q()
    if employee := request.POST.get('employee', None) : query &= Q(id=employee)
    else :
        if company      := request.POST.get('company', None)    : query &= Q(company_id=company)
        if department   := request.POST.get('department', None) : query &= Q(department_id=department)
        if designation  := request.POST.get('designation', None): query &= Q(designation_id=designation)
    attendance_date = request.POST.get('attendance_date', None)
    if attendance_date : 
        attendance_date = datetime.strptime(attendance_date, "%d/%m/%Y")
        date_query &= Q(calendar_day=attendance_date)
    for index, employee in enumerate(EmployeeDetails.objects.filter(query).order_by('personal__employee_id')):
        intime, outtime, work_hrs = '', '', ''
        calendar_log = EmployeeCalendar.objects.filter(date_query & Q(employee=employee)).last()
        shift       = employee.shift.name if employee.shift else ""
        shift_start = employee.shift.start_time.strftime("%I:%M %p") if employee.shift and employee.shift.start_time else ""
        shift_end   = employee.shift.end_time.strftime("%I:%M %p") if employee.shift and employee.shift.end_time else ""
        if not calendar_log :
            calendar_log = EmployeeCalendar.objects.create(calendar_day=attendance_date, employee=employee)
            if str(attendance_date.weekday()) in employee.holiday : calendar_log.is_weekend = True
            else : calendar_log.absent  = True
            calendar_log.save()
        if calendar_log.attendance :
            if intime_data  := calendar_log.attendance.in_time  : 
                intime = intime_data.strftime("%I:%M %p")
            if outtime_data := calendar_log.attendance.out_time : 
                outtime_data = outtime_data.strftime("%I:%M %p")
                if intime != outtime_data : outtime = outtime_data
            if calendar_log.attendance.shift :
                shift       = calendar_log.attendance.shift.name
                shift_start = calendar_log.attendance.shift.start_time.strftime("%I:%M %p") if calendar_log.attendance.shift.start_time else ""
                shift_end   = calendar_log.attendance.shift.end_time.strftime("%I:%M %p") if calendar_log.attendance.shift.end_time else ""
            work_hrs = calendar_log.attendance.work_hours
        data = [int(index) + 1, employee.department.title, employee.designation.name, employee.personal.employee_id, employee.personal.name, shift, shift_start, shift_end, intime or "", outtime or "", work_hrs, calendar_log.day_remarks(),]
        report_data += """<tr>""" + "".join("""<td>{}</td>""".format(d) for d in data) + """</tr>"""
    return JsonResponse({"report_data":report_data}, safe=False)

@login
def get_device_data(request):
    query = """SELECT card.CardID, card.CardTime, card.DevID, device.DevName, device.IPAddress, employee.EmployeeCode, device.Mac, device.Serial, device.DEVTYPESTR FROM [HWATT].[dbo].[KQZ_Card] as card left join [HWATT].[dbo].[KQZ_Employee] as employee on employee.EmployeeID = card.EmployeeID left join [HWATT].[dbo].[KQZ_DevInfo] as device on device.DevID = card.DevID where employee.EmployeeCode = '323494' and card.CardTime >=  '2023-02-01' order by card.CardID asc;"""
    logs = ebs_bl_common.mssql_query(query)
    store_attendance_data(logs)
    return HttpResponse("hi")

def store_attendance_data(logs, user=None):
    attendances = []
    for log in logs:
        if EmployeeDetails.objects.filter(punch_id=log['EmployeeCode']).last(): 
            device, log_time = AttendanceDevice.objects.filter(ip_address=log['IPAddress']).first(), log['CardTime']
            if log_data := AttenddanceLog.objects.filter(punch_id=log['EmployeeCode'], created_by=user, device=device, status=Status.name("Active"), card_id=log['CardID'], log_time=log_time).first() : alog = log_data
            else : alog = AttenddanceLog.objects.create(punch_id=log['EmployeeCode'], created_by=user, device=device, status=Status.name("Active"), card_id=log['CardID'], log_time=log_time)
            if alog and alog.attendance_id : 
                alog.attendance.save()
                attendances.append(alog.attendance_id)
    return attendances


@login
def import_attendances(request):
    if request.method == "POST":
        attendance_list, user = 0, get_object_or_404(Users, pk=request.session.get('id', None))
        import_file = request.FILES['import_file']
        info = pd.read_excel(import_file, 'Sheet1', engine='openpyxl', dtype={'Employee': str})
        from inventory.view.views_item import retrun_str_from_xls as str_from_xls
        for i in range(0, len(info)):
            employee_id = str_from_xls(info['Employee'][i])
            employee_dtl= EmployeeDetails.objects.filter(personal__employee_id=employee_id).last()
            date        = str_from_xls(info['Date'][i], date_field = True)
            outside     = True if str_from_xls(info['Outside Office'][i]).title() == "Yes" else False
            if not outside :
                in_time = str_from_xls(info['In Time'][i], time_field=True)
                out_time= str_from_xls(info['Out Time'][i], time_field=True)
            if employee_dtl and date :
                attn_exist = Attendance.objects.filter(employee=employee_dtl,present_day=date).last()
                has_roaster_shift = HRShiftRoaster.objects.filter(employee=employee_dtl, roaster_date=date).first()
                shift = has_roaster_shift.shift if has_roaster_shift else employee_dtl.shift
                if outside : in_time, out_time = shift.start_time, shift.end_time
                if not attn_exist:
                    Attendance.objects.create(employee=employee_dtl, shift=shift, location=employee_dtl.location, present_day=date,
                        in_time=in_time, out_time=out_time, outside_office=outside, created_by=user, status=Status.name('Active'))
                else :
                    attn_exist.shift    = shift
                    attn_exist.in_time  = in_time
                    attn_exist.out_time = out_time
                    attn_exist.save()
                attendance_list += 1
        messages.success(request, "You have successfully imported {} attendance/s information.".format(attendance_list))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    context = {'title':"Attendance from Device", 'file':'dummy/attendance-template.xlsx'}
    return render(request, 'hr/attendance/import.html', context)

@login
def import_device_data_attendances(request):
    if request.method == 'POST':
        user = get_object_or_404(Users, pk=request.session.get("id"))
        uploaded_file = request.FILES['import_file']
        file_contents = uploaded_file.read().decode('utf-8')
        lines = file_contents.split('\n')
        for line in lines:
            line_data, line_dict = line.split("\" "), {}
            for item in line_data:
                if len(item.split("=")) > 1 :
                    key, value = item.split("=")
                    if key.strip() in ['id', 'time'] : line_dict[key.strip()] = value.strip('"')
            if "time" in line_dict : alog, created = AttenddanceLog.objects.get_or_create(punch_id=line_dict['id'], created_by=user,
                status=Status.name("Active"), device=None, card_id=None, log_time=datetime.strptime(line_dict['time'], '%Y-%m-%d %H:%M:%S'))
        messages.success(request, "You have successfully imported attendance/s information.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    context = {'title':"Attendance from Device", 'file':'dummy/attendance-template.txt'}
    return render(request, 'hr/attendance/import.html', context)


@login
def fetch_attendance_devices(request):
    user = get_object_or_404(Users, pk=request.session.get("id"))
    query = """SELECT device.DevID, device.DevName, device.IPAddress, device.Mac, device.Serial, device.DEVTYPESTR FROM [HWATT].[dbo].[KQZ_DevInfo] as device;"""
    devices, counting = ebs_bl_common.mssql_query(query), 0
    if devices :
        for device in devices:
            if dev := AttendanceDevice.objects.filter(ip_address=device['IPAddress']).first():
                dev.device_type = device['DEVTYPESTR']
                dev.name        = device['DevName']
                dev.Serial      = device['Serial']
                dev.device_id   = device['DevID']
                dev.Mac         = device['Mac']
                dev.save()
            else : AttendanceDevice.objects.create(device_id=device['DevID'], ip_address=device['IPAddress'], Mac=device['Mac'], Serial=device['Serial'], device_type=device['DEVTYPESTR'], name=device['DevName'], created_by=user, status=Status.name("Active"))
            counting += 1
    messages.success(request, "Successfully Updated {} device/s!".format(counting))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login
def attendance_devices(request):
    user = get_object_or_404(Users, pk=request.session.get("id"))
    if request.method == "POST":
        devices = request.POST.getlist("device_id", [])
        devices = AttendanceDevice.objects.filter(id__in=devices)
        for device in devices:
            location = request.POST.get('location[{}]'.format(device.id), None)
            if location : 
                try     : location = Location.objects.get(id=int(location))
                except  : location, created = Location.objects.get_or_create(name=location)
            else : location = None
            building = request.POST.get('building[{}]'.format(device.id), None)
            if building : 
                try     : building = Building.objects.get(id=int(building))
                except  : building, created = Building.objects.get_or_create(location=location, name=building)
            else : building = None
            floor = request.POST.get('floor[{}]'.format(device.id), None)
            if floor : 
                try     : floor = HRFloor.objects.get(id=int(floor))
                except  : floor, created = HRFloor.objects.get_or_create(building=building, name=floor)
            else : floor = None
            device.location, device.building, device.floor = location, building, floor
            device.name = request.POST.get('name[{}]'.format(device.id), None)
            device.updated_by = user
            status = request.POST.get('status[{}]'.format(device.id), 0)
            device.status = Status.name('Inactive') if status == 0 else Status.name('Active')
            device.save()
        messages.success(request, "Successfully updated {} device/s!".format(devices.count()))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
    locations       = Location.objects.filter(status=Status.name("Active"))
    devices         = AttendanceDevice.objects.order_by('device_id')
    template_name   = "hr/attendance/attendance_devices.html"
    context         = { 'devices':devices, 'locations':locations }
    return render(request, template_name, context)

@login
def import_attendance_devices(request):
    if request.method == "POST":
        from inventory.view.views_item import retrun_str_from_xls as str_from_xls
        device_list, user = [], get_object_or_404(Users, pk=request.session.get('id', None))
        import_file = request.FILES['import_file']
        info = pd.read_excel(import_file, 'Sheet1', engine='openpyxl')
        for i in range(0, len(info)):
            location, building, floor = str_from_xls(info['Location'][i]), str_from_xls(info['Building'][i]), str_from_xls(info['Floor'][i])
            if location : location, created = Location.objects.get_or_create(name=location)
            if building : building, created = Building.objects.get_or_create(location=location, name=building)
            if floor    : floor, created    = HRFloor.objects.get_or_create(building=building, name=floor)
            device_id = str_from_xls(info['DevID'][i]) or None
            if device_id :
                name = str_from_xls(info['Name'][i])
                device = AttendanceDevice.objects.filter(device_id=device_id).last()
                if device:
                    device.name, device.updated_by, device.status = name, user, Status.name('Active')
                    device.location, device.building, device.floor = location, building, floor
                    device.save()
                else:
                    ip_address = str_from_xls(info['IP Address'][i]) or None
                    Mac = str_from_xls(info['Mac'][i]) or None
                    Serial = str_from_xls(info['Serial'][i]) or None
                    device_type = str_from_xls(info['Device Type'][i]) or None
                    device = AttendanceDevice.objects.create(device_id=device_id, ip_address=ip_address, Mac=Mac, Serial=Serial, 
                                device_type=device_type, name=name, created_by=user, status=Status.name("Active"))
                if device : device_list.append(device.id)
        messages.success(request, "You have successfully imported {} device/s information.".format(len(set(device_list))))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return render(request, 'hr/attendance/import_devices.html')

@csrf_exempt
def get_attendance_devices(request):
    query, devices = Q(), [{'id':"", "text":""}]
    if floor_id := request.POST.get('floor_id', 0)          : query &= Q(floor_id=floor_id)
    elif building_id := request.POST.get('building_id', 0)  : query &= Q(building_id=building_id)
    elif location_id := request.POST.get('location_id', 0)  : query &= Q(location_id=location_id)
    devices += [{'id':d.device_id, 'text':d.name} for d in AttendanceDevice.objects.filter(query).order_by('device_id')]
    return JsonResponse({'devices':devices}, safe=False)

@login
def sync_attendance(request):   
    devices         = AttendanceDevice.objects.order_by('device_id')
    companies       = Company.objects.filter(status=True).order_by('name')
    departments     = Departments.objects.filter(status = True).order_by('name')
    locations       = Location.objects.filter(status=Status.name("Active"))
    template_name   = "hr/attendance/sync_attendance.html"
    context         = { 'companies':companies, 'locations':locations, 'devices':devices, 'department_list':departments }
    return render(request, template_name, context)

@csrf_exempt
def get_attendance_data_from_devices(request):
    device_ips, device_ip_query = request.POST.getlist('device[]', []), ""
    if not device_ips :
        query = Q()
        if floor := request.POST.get('floor', None): query = Q(floor=floor)
        elif building := request.POST.get('building', None): query = Q(building=building)
        elif location := request.POST.get('location', None): query = Q(location=location)
        device_ips = AttendanceDevice.objects.filter(query).order_by('device_id').values_list("ip_address", flat=True)
    for device_ip in device_ips :
        device_ip_query += "'" + str(device_ip) + "'" + ","
    
    if start_date := request.POST.get('start_date', None): start_date = datetime.strptime(start_date, "%d/%m/%Y")
    if end_date := request.POST.get('end_date', None): end_date = datetime.strptime(end_date, "%d/%m/%Y") + timedelta(days=1)
    
    employee_query, employee_ids = Q(), ''
    if employees  := request.POST.getlist('employee[]')  : employee_query &= Q(id__in=employees)
    if company_id := request.POST.get('company_id', None): employee_query &= Q(company_id=company_id)
    if department := request.POST.get('department', None): employee_query &= Q(department_id=department)
    employees = EmployeeDetails.objects.filter(Q(status=Status.name('active'), shift__isnull=False, punch_id__isnull=False) & employee_query)
    for employee in employees.values_list('punch_id', flat=True) :
        try     : employee_ids += "'" + str(int(float(employee))) + "'"
        except  : employee_ids += "'" + str(employee) + "'"
        employee_ids += ","

    employee_query  = " employee.EmployeeCode in ({}) and ".format(employee_ids.rstrip(','))
    query = """SELECT card.CardID, card.CardTime, device.IPAddress, employee.EmployeeCode FROM [HWATT].[dbo].[KQZ_Card] as card left join [HWATT].[dbo].[KQZ_Employee] as employee on employee.EmployeeID = card.EmployeeID left join [HWATT].[dbo].[KQZ_DevInfo] as device on device.DevID = card.DevID where """ + employee_query + """ card.CardTime >= '{}' and card.CardTime < '{}' and device.IPAddress in ({}) order by card.CardID desc;""".format(start_date.date(), end_date.date(), device_ip_query.rstrip(','))
    attendances = Attendance.objects.none()
    if logs := ebs_bl_common.mssql_query(query) :
        attendances = Attendance.objects.filter(present_day__range=[start_date, end_date], id__in=store_attendance_data(logs, get_object_or_404(Users, pk=request.session.get('id')))).order_by('present_day', 'employee__personal__employee_id')
    current_date = start_date
    while current_date < end_date:
        for emp in employees :
            calendar_log = EmployeeCalendar.objects.filter(employee=emp, calendar_day=current_date.date()).first()
            if not calendar_log : calendar_log = EmployeeCalendar.objects.create(employee=emp, calendar_day=current_date.date(), created_at=datetime.now())
            if str(current_date.weekday()) in emp.holiday : calendar_log.is_weekend = True
            elif HolidayIndividuals.objects.filter( holiday__company=emp.company, holiday_date=current_date.date()).first() : calendar_log.is_holiday = True
            elif calendar_log.attendance_id == None and calendar_log.leave_application_id == None : calendar_log.absent = True
            calendar_log.save()
        current_date += timedelta(days=1)
    return render(request, "hr/attendance/table_data.html", {'attendances':attendances})