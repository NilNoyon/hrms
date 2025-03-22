from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from general.decorators import login, permission
from django.http import JsonResponse
from hr.models import Division, SubSection
from hr.forms import SubSectionForm
from general.models import Status
from django.urls import reverse, reverse_lazy
from django.contrib import messages

from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()

@login
def sub_section_list(request):
    chk_permission = permission(request, reverse('hr:sub_section_list'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                created_by = SubSection._meta.get_field('created_by')
                request.POST['created_by'] = request.session.get('id')
            except : pass
            try :
                status  = SubSection._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = SubSectionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)
        template_name   = "hr/sub_section.html"
        divisions       = Division.objects.filter(status=Status.name("Active"))
        object_list     = SubSection.objects.order_by('id')
        action_url      = reverse_lazy('hr:sub_section_list')
        action_name     = "Add SubSection"
        form            = SubSectionForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'division_list':divisions }
        return render(request, template_name, context)
    else: return redirect(reverse("access_denied"))

@login
def sub_section_update(request, id):
    chk_permission = permission(request, reverse('hr:sub_section_list'))
    if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(SubSection, id=id)
            if request.method == "POST":
                request.POST = request.POST.copy()
                try :
                    updated_by = SubSection._meta.get_field('updated_by')
                    request.POST['updated_by'] = request.session.get('id')
                except : pass
                try :
                    status  = SubSection._meta.get_field('status')
                    status  = request.POST.get('status', 0)
                    request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
                except : pass
                form = SubSectionForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)
            template_name   = "hr/sub_section.html"
            divisions       = Division.objects.filter(status=Status.name("Active"))
            action_name     = "Update SubSection"
            action_url      = reverse_lazy('hr:sub_section_update', kwargs={'id':id})
            object_list     = SubSection.objects.order_by('id')
            form            = SubSectionForm(instance=instance)
            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance, 'division_list':divisions }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('hr:sub_section_list'))
    else: return redirect(reverse("access_denied"))

@login
def sub_section_delete(request, id):
    instance = get_object_or_404(SubSection, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def sub_section_update_status(request):
    instance = get_object_or_404(SubSection, id=request.POST.get('id'))
    print(instance.status)
    instance.status = Status.name('Active') if instance.status is None or instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    print(instance.status)
    return JsonResponse('success', safe=False)