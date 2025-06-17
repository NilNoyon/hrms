from ngoasset.views import *


@login
def vehicle_allocation_list(request):
    # chk_permission = permission(request, reverse('fa:vehicle_allocation_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['created_by'] = request.session.get('id')
        assigned_date   = request.POST.get('assigned_date', '')
        exp_date        = request.POST.get('exp_date', '')
        request.POST['assigned_date']   = datetime.strptime(assigned_date, "%d/%m/%Y") if assigned_date else ''
        request.POST['exp_date']        = datetime.strptime(exp_date, "%d/%m/%Y") if exp_date else ''
        form = VehicleAllocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common_logic.form_errors(request, form)
        
    context = common_context()
    context['tab_name']     = "allocation"
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_allocation_update(request, id):
    # chk_permission = permission(request, reverse('fa:vehicle_allocation_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(VehicleAllocation, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['updated_by'] = request.session.get('id')
            assigned_date   = request.POST.get('assigned_date', '')
            exp_date        = request.POST.get('exp_date', '')
            request.POST['assigned_date']   = datetime.strptime(assigned_date, "%d/%m/%Y") if assigned_date else ''
            request.POST['exp_date']        = datetime.strptime(exp_date, "%d/%m/%Y") if exp_date else ''
            form = VehicleAllocationForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common_logic.form_errors(request, form)

        context = common_context()
        context['tab_name']     = "allocation"
        context['aaction_name'] = "Update Allocation"
        context['aaction_url']  = reverse_lazy('fa:vehicle_allocation_update', kwargs={'id':id})
        context['aform']        = VehicleAllocationForm(instance=instance)
        context['ainstance']    = instance
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('fa:vehicle_allocation_list'))
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_allocation_delete(request, id):
    instance = get_object_or_404(VehicleAllocation, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))