from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from general.models import CommonMaster
from hr.forms import CommonMasterForm
from django.urls import reverse_lazy
from django.contrib import messages


from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def company_unit_list(request):
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['value_for'] = 44
        form = CommonMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/company_unit.html"
    object_list     = CommonMaster.objects.filter(value_for=44).order_by('id')
    action_url      = reverse_lazy('hr:company_unit_list')
    action_name, form = "Add Company Unit", CommonMasterForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)


@login
def company_unit_update(request, id):
    # try:
        instance = CommonMaster.objects.filter(id=id).first()
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['value_for'] = 44
            form = CommonMasterForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/company_unit.html"
        action_name     = "Update Company Unit"
        action_url      = reverse_lazy('hr:company_unit_update', kwargs={'id':id})
        object_list     = CommonMaster.objects.filter(value_for=44).order_by('id')
        form            = CommonMasterForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    # except : return redirect(reverse_lazy('hr:company_unit_list'))


@login
def company_unit_delete(request, id):
    instance = CommonMaster.objects.filter(id=id).first()
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER', '/'))