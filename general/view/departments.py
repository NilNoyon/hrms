from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from general.models import Departments
from general.forms import DepartmentsForm
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def departments_list(request):
    chk_permission = permission(request, reverse('departments_list'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            form = DepartmentsForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        template_name   = "general/departments.html"
        object_list     = Departments.objects.order_by('-id')
        action_url      = reverse_lazy('departments_list')
        action_name     = "Add Departments"
        form            = DepartmentsForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
        return render(request, template_name, context)
    else: return redirect(reverse("access_denied"))

@login
def departments_update(request, id):
    chk_permission = permission(request, reverse('departments_list'))
    if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(Departments, id=id)
            if request.method == "POST":
                form = DepartmentsForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

            template_name   = "general/departments.html"
            action_name     = "Update Departments"
            action_url      = reverse_lazy('departments_update', kwargs={'id':id})
            object_list     = Departments.objects.order_by('id')
            form            = DepartmentsForm(instance=instance)

            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('departments_list'))
    else: return redirect(reverse("access_denied"))

@login
def departments_delete(request, id):
    instance = get_object_or_404(Departments, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))
