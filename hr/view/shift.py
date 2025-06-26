from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from django.views.decorators.csrf import csrf_exempt
from general.models import Company, Status, Departments, Designations
from hr.models import Shift, Location, EmployeeDetails, HRShiftRoaster
from hr.forms import ShiftForm
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.db.models import Q
from general.business_logic import approval_log_logic, common_logic
from django.conf import settings
from datetime import datetime, timedelta

ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def shift_list(request):
    # chk_permission = permission(request, reverse('hr:shift_list'))
    # if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            data = get_formated_data(request)
            form = ShiftForm(data)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/shift.html"
        object_list     = Shift.objects.order_by('id')
        # location_list   = Location.objects.filter(status=Status.name("Active"))
        # company_list    = Company.objects.filter(status=1).order_by('short_name')
        action_url      = reverse_lazy('hr:shift_list')
        action_name     = "Add Shift"
        form            = ShiftForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
        # 'company_list':company_list, 'location_list':location_list }
        return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def shift_update(request, id):
    # chk_permission = permission(request, reverse('hr:shift_list'))
    # if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(Shift, id=id)
            if request.method == "POST":
                data = get_formated_data(request, update=True)
                form = ShiftForm(data, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)

            template_name   = "hr/shift.html"
            action_name     = "Update Shift"
            action_url      = reverse_lazy('hr:shift_update', kwargs={'id':id})
            object_list     = Shift.objects.order_by('id')
            form            = ShiftForm(instance=instance)

            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('hr:shift_list'))
    # else: return redirect(reverse("access_denied"))


@login
def shift_delete(request, id):
    instance = get_object_or_404(Shift, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def shift_update_status(request):
    id = request.POST.get('id')
    instance = get_object_or_404(Shift, id=id)
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return JsonResponse('success', safe=False)

def get_formated_data(request, update=False):
    request.POST = request.POST.copy()
    if update :
        try :
            updated_by = Shift._meta.get_field('updated_by')
            request.POST['updated_by'] = request.session.get('id')
        except : pass
    else :
        try :
            created_by = Shift._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
    try :
        status  = Shift._meta.get_field('status')
        status  = request.POST.get('status', 0)
        request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
    except : pass
    start_time, end_time = request.POST.get('start_time', None), request.POST.get('end_time', None)
    grace_time, day_start = request.POST.get('grace_time', None), request.POST.get('day_start', None)
    buffer_time = request.POST.get('buffer_time', None)
    request.POST['start_time']  = (datetime.strptime(start_time, "%I:%M %p")).strftime("%H:%M:%S") if start_time else ''
    request.POST['end_time']    = (datetime.strptime(end_time, "%I:%M %p")).strftime("%H:%M:%S") if end_time else ''
    request.POST['grace_time']  = (datetime.strptime(grace_time, "%I:%M %p")).strftime("%H:%M:%S") if grace_time else ''
    request.POST['day_start']  = (datetime.strptime(day_start, "%I:%M %p")).strftime("%H:%M:%S") if day_start else ''
    request.POST['buffer_time']  = (datetime.strptime(buffer_time, "%I:%M %p")).strftime("%H:%M:%S") if buffer_time else ''
    return request.POST

def shift_roaster(request):
    if request.method == "POST":
        employee_list   = request.POST.getlist('emp_id', [])
        shift           = request.POST.get('shift', None)
        duration, start_time, end_time = request.POST.get('duration', ''), "", ""
        if duration:
            durations, data_list, delta = duration.split(" - "), [], timedelta(days=1)
            start_time  = datetime.strptime(durations[0], "%Y-%m-%d") if durations[0] else ''
            end_time    = datetime.strptime(durations[1], "%Y-%m-%d") if durations[1] else ''

            for emp in employee_list:
                current_date = start_time
                while current_date <= end_time:
                    if not HRShiftRoaster.objects.filter(employee_id=emp, shift_id=shift, roaster_date=current_date).first() :
                        data = HRShiftRoaster(employee_id=emp, shift_id=shift, roaster_date=current_date, 
                                created_by_id=request.session.get('id', None), status=Status.name("Active"))
                        data_list.append(data)
                    current_date += delta
            HRShiftRoaster.objects.bulk_create(data_list)
            messages.success(request, "Roasters Allocated Successfully!")
            return redirect(request.META.get('HTTP_REFERER', '/'))


    context = { 
        'companies'     : Company.objects.filter(status = True).order_by('name'),
        'designations'  : Designations.objects.filter(status = True).order_by('name'),
        'departments'   : Departments.objects.filter(status = True).order_by('name'), 
        'shifts'        : Shift.objects.filter(status=Status.name('active')) 
    }
    return render(request, "hr/shift_roaster.html", context)

@csrf_exempt
def get_employee_data_for_shift_roaster(request):
    report_data, query = '', Q()
    if company     := request.POST.get('company', None)     : query &= Q(company_id=company)
    if department  := request.POST.get('department', None)  : query &= Q(department_id=department)
    if designation := request.POST.get('designation', None) : query &= Q(designation_id=designation)
    if category_list := request.POST.getlist('category[]', None): query &= Q(employee_category_id__in=category_list)
    if employee_list := request.POST.getlist('employee[]', [])  : query &= Q(id__in=employee_list)
    for employee in EmployeeDetails.objects.filter(query) :
        branch      = employee.branch.short_name if employee.branch_id else ''
        department  = employee.department.title if employee.department_id else ''
        designation = employee.designation.title if employee.designation_id else ''
        employee_id = employee.personal.employee_id if employee.personal_id else ''
        name        = employee.personal.name if employee.personal_id else ''
        shift       = employee.shift if employee.shift_id else ''
        data = [branch, department, designation, employee_id, name, shift]
        report_data += "<tr><td><div class='custom-control custom-checkbox mb-1'>"
        report_data += "<input type='checkbox' class='custom-control-input check_emp'"
        report_data += "name='emp_id' value='" + str(employee.id) + "' id='check-[" + str(employee.id) + "]'>"
        report_data += "<label class='custom-control-label' for='check-[" + str(employee.id) + "]'></label></div></td>"
        report_data += "".join("<td>{}</td>".format(d) for d in data) + "</tr>"
    return JsonResponse({"report_data":report_data}, safe=False)

@csrf_exempt
def get_roasters_for_dataTable(request):
    start, counter = request.POST.get('start', 0), request.POST.get('counter', 0)
    query, content, reset_data, end = Q(status=Status.name("Active")), '', False, int(start) + int(counter)
    
    query_data_list = HRShiftRoaster.objects.filter(query).order_by('-roaster_date')
    total_data, content = query_data_list.count(), ""
    if total_data == 0  : 
        content, reset_data = "<tr><td class='font-weight-bold' colspan='8'>No Data Found!</td></tr>", True
    else :  
        for r in query_data_list[int(start):int(start)+20] :
            company     = r.employee.company.short_name if r.employee and r.employee.company_id else ''
            department  = r.employee.department.title if r.employee and r.employee.department_id else ''
            designation = r.employee.designation.title if r.employee and r.employee.designation_id else ''
            shift       = (r.employee.shift.shift_id + " - " + r.employee.shift.name) if r.employee.shift_id else ''
            created_by  = ebs_bl_common.user_html(r.created_by, 15)
            Roaster_date= str(r.roaster_date.strftime("%d-%b-%Y").upper())
            edit_url    = reverse('hr:roaster_update', kwargs={'id': r.id})
            delete_url  = reverse('hr:roaster_delete', kwargs={'id': r.id})
            edit        = '<a class="h4 m-r-10 text-success edit_btn" href="javascript:void(0);" data-id="' + str(r.id)
            edit       += '" data-url="' + edit_url + '" ><span class="icon"><i class="ti-pencil-alt"></i></span></a>'
            delete      = '<a class="h4 text-danger delete_btn" href="javascript:void(0);" data-url="'
            delete     += delete_url + '"><span class="icon"><i class="ti-trash"></i></span></a>'
            action      = ebs_bl_common.datatable_center_td(edit + delete)
            data = [r.employee.employee_id, r.employee.name, company, department, designation, shift, 
                    r.shift.shift_id + " - " + r.shift.name, Roaster_date, created_by, action]
            content += "<tr>" + "".join("<td>{}</td>".format(str(d)) for d in data) + "</tr>"
    
    if 'true' == request.POST.get('reset', 'false') : reset_data = True
    end_pagination = False if int(end) < int(total_data) else True
    return JsonResponse({ "content":content, "end_pagination":end_pagination, "reset_data":reset_data, "total_data":total_data})


@login
def roaster_update(request, id):
    instance = get_object_or_404(HRShiftRoaster, id=id)
    instance.shift_id = request.POST.get('new_shift', None)
    instance.save()
    messages.success(request, "Successfully Updated!")
    return redirect(request.META.get('HTTP_REFERER'))


@login
def roaster_delete(request, id):
    instance = get_object_or_404(HRShiftRoaster, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))


@csrf_exempt
def get_roaster_data(request):
    instance = get_object_or_404(HRShiftRoaster, id=request.POST.get('id', None))
    return JsonResponse({'emp_id':instance.employee.employee_id, 
        'shift':instance.shift.shift_id + " - " + instance.shift.name})