from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from general.decorators import login, permission
from django.http import JsonResponse
from hr.models import Division, SubSection
from hr.forms import DivisionForm
from django.db.models import F
from general.models import Status
from django.urls import reverse, reverse_lazy
from django.contrib import messages

from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()

@login
def division_list(request):
    chk_permission = permission(request, reverse('hr:division_list'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                created_by = Division._meta.get_field('created_by')
                request.POST['created_by'] = request.session.get('id')
            except : pass
            try :
                status  = Division._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = DivisionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)
        template_name   = "hr/division.html"
        object_list     = Division.objects.order_by('id')
        action_url      = reverse_lazy('hr:division_list')
        action_name     = "Add Division"
        form            = DivisionForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
        return render(request, template_name, context)
    else: return redirect(reverse("access_denied"))
@login
def division_update(request, id):
    chk_permission = permission(request, reverse('hr:division_list'))
    if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(Division, id=id)
            if request.method == "POST":
                request.POST = request.POST.copy()
                try :
                    updated_by = Division._meta.get_field('updated_by')
                    request.POST['updated_by'] = request.session.get('id')
                except : pass
                try :
                    status  = Division._meta.get_field('status')
                    status  = request.POST.get('status', 0)
                    request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
                except : pass
                form = DivisionForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)
            template_name   = "hr/division.html"
            action_name     = "Update Division"
            action_url      = reverse_lazy('hr:division_update', kwargs={'id':id})
            object_list     = Division.objects.order_by('id')
            form            = DivisionForm(instance=instance)
            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('hr:division_list'))
    else: return redirect(reverse("access_denied"))
@login
def division_delete(request, id):
    instance = get_object_or_404(Division, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def division_update_status(request):
    instance = get_object_or_404(Division, id=request.POST.get('id'))
    instance.status = Status.name('Active') if instance.status is None or instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return JsonResponse('success', safe=False)

@csrf_exempt
def get_division_wise_sub_section(request):
    id = request.POST.get('id')
    ss_list = list(SubSection.objects.filter(division_id=id).annotate(text=F('name')).values('id','text'))
    ss_list.insert(0, {'id':'','text':''})
    return JsonResponse({'sub_section':ss_list}, safe=False)