from hr.views import *
from hr.models import HRSalaryCycle
from hr.forms import HRSalaryCycleForm

@login
def hr_salary_cycle_list(request):
    # chk_permission = permission(request, reverse('hr:hr_salary_cycle_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        try :
            created_by = HRSalaryCycle._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
        try :
            status  = HRSalaryCycle._meta.get_field('status')
            status  = request.POST.get('status', 0)
            request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
        except : pass
        request.POST['branch'] = request.POST['company']
        form = HRSalaryCycleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/hr_salary_cycle.html"
    object_list     = HRSalaryCycle.objects.order_by('id')
    action_url      = reverse_lazy('hr:hr_salary_cycle_list')
    action_name     = "Add HRSalaryCycle"
    form            = HRSalaryCycleForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list,
                        'companies'  : Branch.objects.filter(status = True,company_id=request.session.get('company_id')).order_by('name'),
                        'employee_categories' : CommonMaster.objects.filter(value_for=5) }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))

@login
def hr_salary_cycle_update(request, id):
    # chk_permission = permission(request, reverse('hr:hr_salary_cycle_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(HRSalaryCycle, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['branch'] = request.POST['company']
            try :
                updated_by = HRSalaryCycle._meta.get_field('updated_by')
                request.POST['updated_by'] = request.session.get('id')
            except : pass
            try :
                status  = HRSalaryCycle._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = HRSalaryCycleForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/hr_salary_cycle.html"
        action_name     = "Update HRSalaryCycle"
        action_url      = reverse_lazy('hr:hr_salary_cycle_update', kwargs={'id':id})
        object_list     = HRSalaryCycle.objects.order_by('id')
        form            = HRSalaryCycleForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list,
                    'companies'  : Branch.objects.filter(status = True,company_id=request.session.get('company_id')).order_by('name'), 'instance':instance,
                    'employee_categories' : CommonMaster.objects.filter(value_for=5) }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:hr_salary_cycle_list'))
    # else: return redirect(reverse("access_denied"))

@login
def hr_salary_cycle_delete(request, id):
    instance = get_object_or_404(HRSalaryCycle, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))
    
@csrf_exempt
def cycle_update_status(request):
    instance = get_object_or_404(HRSalaryCycle, id=request.POST.get('id'))
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return HttpResponse(instance.status)