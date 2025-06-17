from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from datetime import datetime, timedelta, date
from .forms import HRSalaryBreakdownForm
        
@receiver(post_save, sender=Attendance)
def save_or_create_attendance(sender, instance, created, **kwargs):
    calendar_log = EmployeeCalendar.objects.filter(employee=instance.employee, calendar_day=instance.present_day).first()
    if calendar_log :
        calendar_log.attendance = instance
        calendar_log.absent     = False
        calendar_log.in_leave   = False
        calendar_log.save()
    else : 
        calendar_log = EmployeeCalendar.objects.create(employee=instance.employee, calendar_day=instance.present_day, attendance=instance, created_at=datetime.now())
    
    if instance.outside_office : calendar_log.outside_duty = True
    if holiday := HolidayIndividuals.objects.filter(holiday_date=instance.present_day, 
        holiday__branch=instance.employee.branch).first() :
        if holiday.holiday.weekend : calendar_log.is_weekend = True
        else : calendar_log.is_holiday = True

    has_roaster_shift = HRShiftRoaster.objects.filter(employee=instance.employee, roaster_date=instance.present_day).first()
    shift = has_roaster_shift.shift if has_roaster_shift else instance.shift
    if instance.in_time and isinstance(instance.in_time, datetime):
        instance.in_time = instance.in_time.time()
    if shift and shift.id and shift.grace_time and instance.in_time \
        and (instance.in_time > shift.grace_time) : calendar_log.is_late = True
    calendar_log.save()


@receiver(post_save, sender=HRLeaveApplication)
def save_or_create_leave_application(sender, instance, created, **kwargs):
    if instance.status == Status.name('Approved'):
        delta, start_date, end_date = timedelta(days=1), instance.start_date, instance.end_date
        while start_date <= end_date:
            if calendar_log := EmployeeCalendar.objects.filter(employee=instance.employee,calendar_day=start_date).first() :
                calendar_log.absent = False
                calendar_log.in_leave = True
                calendar_log.leave_application = instance
                calendar_log.save()
            else : EmployeeCalendar.objects.create(employee=instance.employee, calendar_day=start_date, 
                    in_leave=True, leave_application=instance, created_at=datetime.now())
            start_date += delta

@receiver(post_save, sender=EmployeeDetails)
def save_or_create_employee_details(sender, instance, created, **kwargs):
    if instance.employee_category_id and instance.salary :
        from decimal import Decimal
        slab_heads = HRSalarySlabMaster.objects.filter(slab=instance.employee_category, type__icontains = 'A').order_by('value_percentage')
        for i in slab_heads :
            salary = int(instance.salary)
            if i.slab.value == 'Worker' :
                gross_salary    = salary - 1850
            else: gross_salary  = salary
            if "V" in i.type    : amount = i.value_percentage
            elif "P" in i.type  : amount = Decimal(gross_salary) * Decimal(i.value_percentage / 100)
            try     : amount = round(amount, 0)
            except  : amount = 0
            if iexist := HRSalaryBreakdown.objects.filter(slab_heads=i, employee=instance).first() :
                iexist.amount = amount
                iexist.save()
            else : HRSalaryBreakdown.objects.create(slab_heads=i, employee=instance, amount=amount)
        
        if instance.income_tax :
            itds_data, created = CommonMaster.objects.get_or_create(value_for=47, value='ITDS')
            itds, created = HRSalarySlabMaster.objects.get_or_create(slab=instance.employee_category, head=itds_data, type='DV')
            iexist = HRSalaryBreakdown.objects.filter(slab_heads=itds, employee=instance).first()
            if tax_value := HRIncomeTaxSlabMaster.objects.filter(from_amount__lte=instance.salary, to_amount__gte=instance.salary).first() :
                print(tax_value.deduction)
                if iexist :
                    iexist.amount = tax_value.deduction
                    iexist.save()
                else : HRSalaryBreakdown.objects.create(slab_heads=itds, employee=instance, amount=tax_value.deduction)
            elif iexist :
                iexist.amount = 0
                iexist.save()