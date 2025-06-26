from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from django.views.decorators.csrf import csrf_exempt
from general.models import Branch, Status
from hr.models import Location
from hr.forms import LocationForm
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def location_list(request):
    chk_permission = permission(request, reverse('hr:location_list'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                created_by = Location._meta.get_field('created_by')
                request.POST['created_by'] = request.session.get('id')
            except : pass
            try :
                status  = Location._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = LocationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")

            else : ebs_bl_common.form_errors(request, form)


        template_name   = "hr/location.html"
        object_list     = Location.objects.order_by('id')
        branch_list     = Branch.objects.order_by('id')
        action_url      = reverse_lazy('hr:location_list')
        action_name     = "Add Location"
        form            = LocationForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'branch_list':branch_list }
        return render(request, template_name, context)
    else: return redirect(reverse("access_denied"))


@login
def location_update(request, id):
    chk_permission = permission(request, reverse('hr:location_list'))
    if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(Location, id=id)
            if request.method == "POST":
                request.POST = request.POST.copy()
                try :
                    updated_by = Location._meta.get_field('updated_by')
                    request.POST['updated_by'] = request.session.get('id')
                except : pass
                try :
                    status  = Location._meta.get_field('status')
                    status  = request.POST.get('status', 0)
                    request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
                except : pass
                form = LocationForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)


            template_name   = "hr/location.html"
            action_name     = "Update Location"
            action_url      = reverse_lazy('hr:location_update', kwargs={'id':id})
            object_list     = Location.objects.order_by('id')
            form            = LocationForm(instance=instance)
            branch_list     = Branch.objects.order_by('id')

            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance, 'branch_list':branch_list }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('hr:location_list'))
    else: return redirect(reverse("access_denied"))


@login
def location_delete(request, id):
    instance = get_object_or_404(Location, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def location_update_status(request):
    id = request.POST.get('id')
    instance = get_object_or_404(Location, id=id)
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return JsonResponse('success', safe=False)