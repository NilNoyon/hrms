from cmath import nan
from datetime import date, datetime , timedelta
from general.decorators import login, permission
from general.models import Company, Designations, Status
from hr.forms import PFLoanForm, PFLoanResheduleForm
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse, resolve_url
import os
from django.db.models import Q
from django.shortcuts import render
from datetime import date
from dateutil import relativedelta
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
from hr.models import EmployeePF, PFLoanSetup

def loan_eligible_list(request):
    chk_permission   = permission(request,  reverse('hr:loan_eligible_list'))
    if chk_permission:
            loan_list = PFLoanSetup.objects.values_list('employee_id', flat=True)
            employee_eligible = EmployeePF.objects.filter(status = Status.name('active'))
            emply_data_list=[]
            request.session['employee_pf'] = " "
            for data in employee_eligible: 
                pf_membership_date = data.date_Pf_membership
                to_date = datetime.now().date()
                date1 = datetime(pf_membership_date.year, pf_membership_date.month, pf_membership_date.day)
                date2 = datetime(to_date.year, to_date.month, to_date.day)
                diff = relativedelta.relativedelta(date1, date2)
                year = abs(int(diff.years)) 
                month = abs(int(diff.months))
                day = abs(int(diff.days))
                tenure = str(year)+ " years "+str(month) + " month "+str(day)+" days"
                if year >= 1:
                    pf_obj={
                        'id' : data.id,
                        'employee_id':data.employee.employee_id,
                        'name': data.employee.name,
                        'date_Pf_membership' : data.date_Pf_membership,
                        'company' : data.employee.company.name,
                        'department' : data.employee.department.name,
                        'designation' : data.employee.designation.name,
                        'pf' : data.pf.pf_heading,
                        'tenure' : tenure
                    }
                    emply_data_list.append(pf_obj)
            context = {
                'emply_data_list' : emply_data_list,  
                }
            return render (request, 'pf/loan/loan_eligible_list.html', context)
    else:
        return redirect('/access-denied')


def loan_list(request):
    chk_permission   = permission(request, reverse('hr:loan_list'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.session["role_text"].lower() in ["admin", "super admin"]: 
            loan_list = PFLoanSetup.objects.all()
        else:
            loan_list = PFLoanSetup.objects.filter(company_id = request.session.get('company_id'))

        company_list  = Company.objects.filter(status = True)
        designation_list = Designations.objects.filter(status = True)
        context = {
            'loan_list' : loan_list,
            'company_list': company_list,
            'designation_list' : designation_list
        }
        return render(request, 'pf/loan/loan_list.html', context)
    else:
        return redirect('/access-denied')


def pf_loan_setup(request, id):
    chk_permission   = permission(request, reverse('hr:loan_eligible_list'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        request.session['employee_loan'] = "save_loan"
        instance = get_object_or_404(EmployeePF, id=id)
        if instance:
            if request.method == 'POST':
                request.POST  =  request.POST.copy()
                request.POST['pf'] = instance.id
                request.POST['employee'] = instance.employee
                request.POST['emi_start_date'] = datetime.strptime(request.POST.get('emi_start_date'), "%d-%b-%Y").date() if request.POST.get('emi_start_date') else ''
                form = PFLoanForm(request.POST)
                if form.is_valid():
                    form.save()
                    request.session['loan'] = None
                    msg = "Loan allocate successfull"
                    messages.success(request,msg)
                else:
                    for field in form:
                            for error in field.errors:
                                messages.warning(request, "%s : %s" % (field.name, error))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                action = {'name': 'Add New', 'btnTxt': 'Submit'}
                context = {
                    "action" : action,
                    "instance" : instance,
                }
                return render(request, "pf/loan/loan_setup.html" , context)
        else:
            messages.warning(request,"")
            return redirect('hr:')
    else:
        return redirect('/access-denied')


def pf_loan_update(request, id):
    chk_permission   = permission(request, reverse('hr:loan_eligible_list'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        request.session['employee_loan'] = "save_loan"
        instance = get_object_or_404(PFLoanSetup, id = id)
        print("instance",instance)
        if instance:
            if request.method == 'POST':
                request.POST  =  request.POST.copy()
                request.POST['pf'] = instance.pf
                request.POST['employee'] = instance.employee
                request.POST['emi_start_date'] = datetime.strptime(request.POST.get('emi_start_date'), "%d-%b-%Y").date() if request.POST.get('emi_start_date') else ''
                form = PFLoanForm(request.POST, instance = instance)
                if form.is_valid():
                    form.save()
                    request.session['loan'] = None
                    msg = "Loan successfull Updated"
                    messages.success(request,msg)
                else:
                    for field in form:
                            for error in field.errors:
                                messages.warning(request, "%s : %s" % (field.name, error))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                action = {'name': 'Add New', 'btnTxt': 'Update'}
                context = {
                    "action" : action,
                    "loan_instance" : instance,
                }
                return render(request, "pf/loan/loan_setup.html" , context)
        else:
            messages.warning(request,"")
            return redirect('hr:')
    else:
        return redirect('/access-denied')

def loan_schedule(request, id):
    chk_permission   = permission(request, reverse('hr:loan_eligible_list'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.session["role_text"].lower() in ["admin", "super admin"]: 
            instance = get_object_or_404(PFLoanSetup, id = id)

            context = {
                'loan_instance' : instance,
            }
            return render(request, 'pf/loan/loan_schedule.html', context)
    else:
        return redirect('/access-denied')

def loan_reschedule(request, id):
    chk_permission   = permission(request, reverse('hr:loan_eligible_list'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.session["role_text"].lower() in ["admin", "super admin"]:
            instance = get_object_or_404(PFLoanSetup, id = id)
            if request.method == 'POST':
                request.POST = request.POST.copy()
                form = PFLoanResheduleForm (request.POST)
                print("form: ",form)
                if form.is_valid():
                    obj = form.save()
                    if obj:PFLoanSetup.objects.filter(id = instance.id).update(rescheduled_counter = F("rescheduled_counter") + 1)
                    msg = "Loan successfull Updated"
                    messages.success(request,msg)
                else:
                    for field in form:
                            for error in field.errors:
                                messages.warning(request, "%s : %s" % (field.name, error))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            else:
                action = {'name': 'Add New', 'btnTxt': 'Reschedule'}
                # loan_instance = PFLoanSetup.objects.all()
                context = {
                    'action' :action,
                    'loan_instance' : instance,
                }
            return render(request, 'pf/loan/loan_reschedule.html', context)
    else:
        return redirect('/access-denied')

# @csrf_exempt
# def get_loan_info(request):
#     if request.POST.get('employee'):
#         loan_info = PFLoanSetup.objects.filter(id=int(request.POST.get('employee'))).first()
#         data = {
#            'interest_rate' : loan_info.interest_rate,
#         }
#         return JsonResponse(data, safe=False)
#     else:
#         return JsonResponse("Something went wrong!", safe=False)


@csrf_exempt
def get_loan_filter(request):
    data_list = []
    search_text = request.POST.get('search_text','').strip()
    start       = int(request.POST.get('start', 0))
    company     = request.POST.get('company','')
    designation = request.POST.get('designation','')
    start_date  = request.POST.get('start_date', '')
    end_date    = request.POST.get('end_date', '') 
    if request.session["role_text"].lower() in  ['admin', 'super admin',]:
        loan_list= PFLoanSetup.objects.all()
    else:
        loan_list = PFLoanSetup.objects.filter(company_id = request.session.get('company_id'))

    if search_text: loan_list = loan_list.filter(Q(loan_amount__icontains=search_text)|Q(emi_months__icontains=search_text)|Q(interest_rate__icontains=search_text)|Q(employee__employee_id__icontains=search_text)|Q(employee__name__icontains=search_text))
    if start_date or end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date + timedelta(days=1)
        loan_list = loan_list.filter(created_at__gte=start_date, created_at__lt=end_date)

    if company: loan_list = loan_list.filter(pf__employee__company = company)
    if designation: loan_list = loan_list.filter(pf__employee__designation = designation)

    loan_list = loan_list[start:start + 20]
    for loan in loan_list:
        employee = loan.pf.employee.employee_id if loan.pf.employee else 'N/A'
        name     = loan.pf.employee.name if loan.pf.employee.name else 'N/A' 
        company  = loan.pf.employee.company if loan.pf.employee.company else 'N/A'
        designation = loan.pf.employee.designation if loan.pf.employee.designation else 'N/A'
        created_at = loan.created_at.strftime("%d-%b-%Y").upper() if loan.created_at else 'N/A'
        interest_rate = loan.interest_rate if loan.interest_rate else 'N/A'
        loan_amount = loan.loan_amount if loan.loan_amount else 'N/A'
        emi_months = loan.emi_months if loan.emi_months else 'N/A'
        emi_start_date = loan.emi_start_date.strftime("%d-%b-%Y").upper() if loan.emi_start_date else 'N/A'
        rescheduled_counter = loan.rescheduled_counter if loan.rescheduled_counter else 'N/A' 
        action =""   
        edit_url = reverse('hr:loan_update', kwargs={'id': loan.id})
        edit = '<a class="h4 m-r-10 text-success" href="' + edit_url + '" class="h4 text-danger" title="Update">'
        edit += '<span class="icon"><i class="ti-pencil-alt"></i></span></a>'
        action += edit

        view_url = reverse('hr:loan_schedule', kwargs={'id': loan.id})
        view = '<a class="h4 m-r-10 text-info" href="' + view_url + '" class="h4 text-danger" title="View">'
        view += '<span class="icon"><i class="icon-eye"></i></span></a>'
        action += view

        schedule_url = reverse('hr:loan_reschedule', kwargs={'id': loan.id})
        schedule = '<a class="h4 m-r-10 text-success" href="' + schedule_url + '" class="h4 text-danger" title="View">'
        schedule += '<span class="icon"><i class="fas fa-undo"></i></span></a>'
        action += schedule

        data = [employee,name,str(company),str(designation),created_at,interest_rate,loan_amount,emi_months,emi_start_date,rescheduled_counter,action]
        data_list.append(data)

    return JsonResponse(data_list, safe=False)


