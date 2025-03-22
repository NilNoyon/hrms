from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from general.models import Status
from hr.models import HRFloor, Building
from hr.forms import HRFloorForm
from django.urls import reverse_lazy
from django.contrib import messages


from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def hr_floor_list(request):
    if request.method == "POST":
        request.POST = request.POST.copy()
        try :
            created_by = HRFloor._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
        try :
            status  = HRFloor._meta.get_field('status')
            status  = request.POST.get('status', 0)
            request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
        except : pass
        form = HRFloorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/hr_floor.html"
    building_list   = Building.objects.filter(status=Status.name("Active")).order_by('id')
    object_list     = HRFloor.objects.order_by('id')
    action_url      = reverse_lazy('hr:hr_floor_list')
    action_name, form = "Add HRFloor", HRFloorForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'building_list':building_list }
    return render(request, template_name, context)


@login
def hr_floor_update(request, id):
    try:
        instance = get_object_or_404(HRFloor, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                updated_by = HRFloor._meta.get_field('updated_by')
                request.POST['updated_by'] = request.session.get('id')
            except : pass
            try :
                status  = HRFloor._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = HRFloorForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/hr_floor.html"
        action_name     = "Update HRFloor"
        building_list   = Building.objects.filter(status=Status.name("Active")).order_by('id')
        action_url      = reverse_lazy('hr:hr_floor_update', kwargs={'id':id})
        object_list     = HRFloor.objects.order_by('id')
        form            = HRFloorForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance, 'building_list':building_list }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:hr_floor_list'))


@login
def hr_floor_delete(request, id):
    instance = get_object_or_404(HRFloor, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))