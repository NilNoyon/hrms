from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from general.decorators import login, permission
from django.views.decorators.csrf import csrf_exempt
from hr.models import FiscalYear
from hr.forms import FiscalYearForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from general.models import Status

from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()

@login
def fiscal_year_list(request):
    # chk_permission = permission(request, reverse('hr:fiscal_year_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()

        overlapping_years = FiscalYear.objects.filter(Q(start_date__lte=request.POST['end_date']) & Q(end_date__gte=request.POST['start_date']))

        if overlapping_years.exists():
            messages.warning(request, "The date range conflicts with an existing fiscal year: {}!".format(overlapping_years.first().name))
            return redirect(reverse_lazy('hr:fiscal_year_list'))

        # Ensure start_date is before end_date
        if request.POST['start_date'] >= request.POST['end_date']:
            messages.warning(request, "The start date must be before the end date!")
            return redirect(reverse_lazy('hr:fiscal_year_list'))

        try :
            created_by = FiscalYear._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
        try :
            status  = FiscalYear._meta.get_field('status')
            status  = request.POST.get('status', 0)
            request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
        except : pass
        form = FiscalYearForm(request.POST)
        if form.is_valid():
            instance = form.save()
            messages.success(request, "Successfully Stored!")
            if instance.status == Status.name('Active'): FiscalYear.objects.exclude(id=instance.id).update(status=Status.name('Inactive'))
            return redirect(reverse_lazy('hr:fiscal_year_list'))
        else : ebs_bl_common.form_errors(request, form)
    template_name   = "hr/fiscal_year.html"
    object_list     = FiscalYear.objects.order_by('id')
    action_url      = reverse_lazy('hr:fiscal_year_list')
    action_name     = "Add FiscalYear"
    form            = FiscalYearForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))

@login
def fiscal_year_update(request, id):
    # chk_permission = permission(request, reverse('hr:fiscal_year_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(FiscalYear, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            
            overlapping_years = FiscalYear.objects.filter(Q(start_date__lte=request.POST['end_date']) & Q(end_date__gte=request.POST['start_date'])).exclude(id=id)

            if overlapping_years.exists():
                messages.warning(request, "The date range conflicts with an existing fiscal year: {}!".format(overlapping_years.first().name))
                return redirect(reverse_lazy('hr:fiscal_year_list'))

            # Ensure start_date is before end_date
            if request.POST['start_date'] >= request.POST['end_date']:
                messages.warning(request, "The start date must be before the end date!")
                return redirect(reverse_lazy('hr:fiscal_year_list'))
            
            try :
                updated_by = FiscalYear._meta.get_field('updated_by')
                request.POST['updated_by'] = request.session.get('id')
            except : pass
            try :
                status  = FiscalYear._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = FiscalYearForm(request.POST, instance=instance)
            if form.is_valid():
                instance = form.save()
                messages.success(request, "Successfully Updated!")
                if instance.status == Status.name('Active'): FiscalYear.objects.exclude(id=instance.id).update(status=Status.name('Inactive'))
                return redirect(reverse_lazy('hr:fiscal_year_list'))
            else : ebs_bl_common.form_errors(request, form)
        template_name   = "hr/fiscal_year.html"
        action_name     = "Update FiscalYear"
        action_url      = reverse_lazy('hr:fiscal_year_update', kwargs={'id':id})
        object_list     = FiscalYear.objects.order_by('id')
        form            = FiscalYearForm(instance=instance)
        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:fiscal_year_list'))
    # else: return redirect(reverse("access_denied"))

@login
def fiscal_year_delete(request, id):
    instance = get_object_or_404(FiscalYear, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def fiscal_year_update_status(request):
    id = request.POST.get('id')
    instance = get_object_or_404(FiscalYear, id=id)
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    if instance.status == Status.name('Active'): FiscalYear.objects.exclude(id=id).update(status=Status.name('Inactive'))
    return JsonResponse('success', safe=False)