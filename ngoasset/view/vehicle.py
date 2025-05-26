from ngoasset.views import *


@login
def vehicle_list(request):
    # chk_permission = permission(request, reverse('fa:vehicle_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['created_by'] = request.session.get('id')
        reg_exp_date            = request.POST.get('reg_exp_date', '')
        fitness_exp_date        = request.POST.get('fitness_exp_date', '')
        rent_date               = request.POST.get('rent_date', '')
        driver_assigned_date    = request.POST.get('driver_assigned_date', '')
        request.POST['reg_exp_date']            = datetime.strptime(reg_exp_date, "%d/%m/%Y") if reg_exp_date else ''
        request.POST['fitness_exp_date']        = datetime.strptime(fitness_exp_date, "%d/%m/%Y") if fitness_exp_date else ''
        request.POST['rent_date']               = datetime.strptime(rent_date, "%d/%m/%Y") if rent_date else ''
        request.POST['driver_assigned_date']    = datetime.strptime(driver_assigned_date, "%d/%m/%Y") if driver_assigned_date else ''
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common_logic.form_errors(request, form)

    return render(request, template_name, common_context())
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_update(request, id):
    # chk_permission = permission(request, reverse('fa:vehicle_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(Vehicle, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['updated_by'] = request.session.get('id')
            reg_exp_date            = request.POST.get('reg_exp_date', '')
            fitness_exp_date        = request.POST.get('fitness_exp_date', '')
            rent_date               = request.POST.get('rent_date', '')
            driver_assigned_date    = request.POST.get('driver_assigned_date', '')
            request.POST['reg_exp_date']            = datetime.strptime(reg_exp_date, "%d/%m/%Y") if reg_exp_date else ''
            request.POST['fitness_exp_date']        = datetime.strptime(fitness_exp_date, "%d/%m/%Y") if fitness_exp_date else ''
            request.POST['rent_date']               = datetime.strptime(rent_date, "%d/%m/%Y") if rent_date else ''
            request.POST['driver_assigned_date']    = datetime.strptime(driver_assigned_date, "%d/%m/%Y") if driver_assigned_date else ''
            form = VehicleForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common_logic.form_errors(request, form)

        context = common_context()
        context['vaction_name'] = "Update Vehicle"
        context['vaction_url']  = reverse_lazy('fa:vehicle_update', kwargs={'id':id})
        context['vform']        = VehicleForm(instance=instance)
        context['vinstance']    = instance
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('fa:vehicle_list'))
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_delete(request, id):
    instance = get_object_or_404(Vehicle, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))