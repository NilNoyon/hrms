#from celery import task
from ebs.celery import app
from datetime import datetime, timedelta, date
from celery import shared_task
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

# Business Logic
from general.business_logic import common_logic
ebs_bl_common = common_logic.Common()
from hr.view.attendance import store_attendance_data
from hr.models import EmployeeCalendar, AttenddanceLog, EmployeeDetails, EmployeeCalendar, HRSalaryCycle, HRSalaryBreakdown, HRSalaryProcess, HolidayIndividuals
from general.models import Status
from hr.views import salary_details_entry



@app.task(name='hr.tasks.load_attendance_data')
def load_attendance_data():
    current_time= datetime.now()
    start_date  = current_time - timedelta(days=1)
    # start_date  = datetime(date.today().year, date.today().month - 1, 1)
    end_date    = current_time + timedelta(days=1)

    employee_ids, card_id = "", 0
    if last_log := AttenddanceLog.objects.order_by('-card_id').first() : card_id = last_log.card_id
    employees = EmployeeDetails.objects.filter(status=Status.name('active'),
         punch_id__isnull=False, shift__isnull=False).values_list('punch_id', flat=True)
    for index, e in enumerate(employees) :
        try     : 
            e_id = str(int(float(e)))
            if index != 0 and len(employee_ids) != 0 : employee_ids += ","
            employee_ids += "'" + str(e_id) + "'"
        except  : pass
    employee_query  = " employee.EmployeeCode in ({})".format(employee_ids)
    card_query = " and card.CardTime >= '{}' and card.CardTime < '{}' and card.CardID > '{}'".format(start_date.date(), end_date.date(), card_id)
    # card_query = " and card.CardTime >= '{}' and card.CardID > '{}'".format(datetime(date.today().year, date.today().month - 1, 1), card_id)
    
    query = """SELECT card.CardID, card.CardTime, device.DevID,
        employee.EmployeeCode FROM [HWATT].[dbo].[KQZ_Card] as card
        left join [dbo].[KQZ_Employee] as employee on employee.EmployeeID = card.EmployeeID
        left join [dbo].[KQZ_DevInfo] as device on device.DevID = card.DevID 
        where """ + employee_query + card_query + """ order by card.CardID asc;"""
    
    if logs := ebs_bl_common.mssql_query(query) : store_attendance_data(logs)
    
    for rdate in [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)] :
        todays_missing_data(rdate)

@app.task(name='hr.tasks.todays_missing_data')
def todays_missing_data(date_val = ''):
    if not date_val : date_val = datetime.today()
    employees = EmployeeDetails.objects.filter(status=Status.name('active')).order_by('personal__employee_id')
    # Weekend Declare
    for employee in employees.filter(holiday__contains=[str(date_val.weekday())]) :
        if emp_cal := EmployeeCalendar.objects.filter(employee=employee, calendar_day=date_val).first() : 
            emp_cal.is_weekend = True
            emp_cal.save()
        else : EmployeeCalendar.objects.create(employee=employee, calendar_day=date_val, is_weekend=True, created_at=datetime.now())
    # Holiday Declare
    for holiday in HolidayIndividuals.objects.filter(holiday_date=date_val):
        for employee in employees.filter(company=holiday.holiday.company) :
            if emp_cal := EmployeeCalendar.objects.filter(employee=employee, calendar_day=date_val).first() : 
                if not emp_cal.is_weekend : emp_cal.is_holiday = True
                emp_cal.save()
            else : EmployeeCalendar.objects.create(employee=employee, calendar_day=date_val, is_holiday=True, created_at=datetime.now())
    # Absent/Late Declare
    for employee in employees:
        if emp_cal := EmployeeCalendar.objects.filter(employee=employee, calendar_day=date_val).first() :
            if emp_cal.attendance and emp_cal.attendance.in_time and emp_cal.attendance.shift and emp_cal.attendance.shift.grace_time \
                and emp_cal.attendance.in_time > emp_cal.attendance.shift.grace_time :
                emp_cal.is_late = True
            if emp_cal.attendance or emp_cal.is_weekend or emp_cal.is_holiday or emp_cal.in_leave\
                or emp_cal.in_roaster or emp_cal.outside_duty : emp_cal.absent = False
            else : emp_cal.absent = True
            emp_cal.save()
        else : EmployeeCalendar.objects.create(employee=employee, calendar_day=date_val, absent=True, created_at=datetime.now())


@app.task(name='hr.tasks.missing_data')
def missing_data():
    start_date, end_date = datetime(date.today().year, date.today().month, 1), datetime.now()
    for rdate in [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)] :
        todays_missing_data(rdate)
    

@shared_task
def process_salary(sp_id=None):
    salary_process = get_object_or_404(HRSalaryProcess, pk=sp_id)
    num_of_days, per_day_amount, basic, user = 30, 0, 0, salary_process.created_by
    for employee in salary_process.employees.all():
        if salary_cycle := HRSalaryCycle.objects.filter(company=employee.company, employee_category=employee.employee_category).first() :
            if salary_cycle.start_date != 1 : 
                start_date          = datetime(salary_process.year, salary_process.month-1, salary_cycle.start_date, 0, 0, 0)
                end_date            = datetime(salary_process.year, salary_process.month, salary_cycle.end_date, 0, 0, 0)
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
            print("abs : ", absent_days, "pa : ", per_day_amount)
            if absent_days and per_day_amount :
                absent_days = absent_days if absent_days < num_of_days else num_of_days
                amount = round(per_day_amount * absent_days, 0)
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, head_name="Absent", head_type="DV", user=user)
            
            # Holiday Payment
            if holidays := EmployeeCalendar.objects.filter(Q(Q(is_holiday=True)|Q(is_weekend=True)), 
                            Q(employee=employee, employee__holiday_bonus=True, 
                                calendar_day__month=salary_process.month, calendar_day__year=salary_process.year)).count() :
                amount = round(per_day_amount * holidays * 2, 0)
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, head_name="Holiday", head_type="AV", user=user)
            
            # OT Payment
            ot_hours_obj = EmployeeCalendar.objects.filter(employee=employee, employee__overtime=True, 
                calendar_day__month=salary_process.month, calendar_day__year=salary_process.year).annotate(total_ot=Sum('attendance__ot_hours'))
            if ot_hours_obj.count() :
                ot_hours = sum(o.total_ot for o in ot_hours_obj if o.total_ot)
                amount = round((basic / 206) * ot_hours * 2, 0) # 208 = 26 days * 8 hours per day
                salary_details_entry(year=salary_process.year, month=salary_process.month, amount=amount, employee=employee, head_name="Over Time", head_type="AV", user=user)
    
    salary_process.status = Status.name('completed')
    salary_process.save()
