from ngoasset.views import *


@login
def vehicle_service_list(request):
    # chk_permission = permission(request, reverse('fa:vehicle_service_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST    = request.POST.copy()
        request.POST['created_by'] = request.session.get('id')
        repair_date     = request.POST.get('repair_date', '')
        request.POST['repair_date']   = datetime.strptime(repair_date, "%d/%m/%Y") if repair_date else ''
        form = VehicleServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common_logic.form_errors(request, form)
        
    context = common_context()
    context['tab_name'] = "service"
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_service_update(request, id):
    # chk_permission = permission(request, reverse('fa:vehicle_service_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(VehicleService, id=id)
        if request.method == "POST":
            request.POST    = request.POST.copy()
            request.POST['updated_by'] = request.session.get('id')
            repair_date     = request.POST.get('repair_date', '')
            request.POST['repair_date']   = datetime.strptime(repair_date, "%d/%m/%Y") if repair_date else ''
            form = VehicleServiceForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common_logic.form_errors(request, form)
            
        context = common_context()
        context['tab_name']     = "service"
        context['saction_name'] = "Update Service"
        context['saction_url']  = reverse_lazy('fa:vehicle_service_update', kwargs={'id':id})
        context['sform']        = VehicleServiceForm(instance=instance)
        context['sinstance']    = instance
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('fa:vehicle_service_list'))
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_service_delete(request, id):
    instance = get_object_or_404(VehicleService, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))