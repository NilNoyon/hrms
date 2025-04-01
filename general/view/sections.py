from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from general.models import Departments, Sections, Status
from general.forms import SectionsForm
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def sections_list(request):
    chk_permission = permission(request, reverse('sections_list'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                created_by = Sections._meta.get_field('created_by')
                request.POST['created_by'] = request.session.get('id')
            except : pass
            try :
                status  = Sections._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Active') if request.POST["status"] == 'on' else Status.name('Inactive')
            except : pass
            form = SectionsForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


        template_name   = "general/sections.html"
        object_list     = Sections.objects.order_by('id')
        department_list = Departments.objects.order_by('id')
        action_url      = reverse_lazy('sections_list')
        action_name     = "Add Sections"
        form            = SectionsForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list,'department_list':department_list }
        return render(request, template_name, context)
    else: return redirect(reverse("access_denied"))



@login
def sections_update(request, id):
    chk_permission = permission(request, reverse('sections_list'))
    if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(Sections, id=id)
            if request.method == "POST":
                request.POST = request.POST.copy()
                try :
                    updated_by = Sections._meta.get_field('updated_by')
                    request.POST['updated_by'] = request.session.get('id')
                except : pass
                try :
                    status  = Sections._meta.get_field('status')
                    status  = request.POST.get('status', 0)
                    request.POST['status'] = Status.name('Active') if request.POST["status"] == 'on' else Status.name('Inactive')
                except : pass
                form = SectionsForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

            template_name   = "general/sections.html"
            action_name     = "Update Sections"
            action_url      = reverse_lazy('sections_update', kwargs={'id':id})
            object_list     = Sections.objects.order_by('id')
            department_list = Departments.objects.order_by('id')
            form            = SectionsForm(instance=instance)

            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance,'department_list':department_list }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('sections_list'))
    else: return redirect(reverse("access_denied"))

@login
def sections_delete(request, id):
    instance = get_object_or_404(Sections, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))