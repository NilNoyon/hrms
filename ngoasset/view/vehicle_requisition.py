from fixedasset.views import *


@login
def vehicle_requisition_list(request):
    # chk_permission = permission(request, reverse('fa:vehicle_requisition_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST    = request.POST.copy()
        request.POST['created_by'] = request.session.get('id')
        req_date        = request.POST.get('req_date', '')
        request.POST['req_date']   = datetime.strptime(req_date, "%d/%m/%Y") if req_date else ''
        req_duration    = request.POST.get('req_duration', '')
        if req_duration:
            durations = req_duration.split(" - ")
            request.POST['start_time']  = datetime.strptime(durations[0], "%d/%m/%Y %I:%M %p") if durations[0] else ''
            request.POST['end_time']    = datetime.strptime(durations[1], "%d/%m/%Y %I:%M %p") if durations[1] else ''
        form = VehicleRequisitionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common_logic.form_errors(request, form)
        
    context = common_context()
    context['tab_name'] = "requisition"
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_requisition_update(request, id):
    # chk_permission = permission(request, reverse('fa:vehicle_requisition_list'))
    # if chk_permission and chk_permission.view_action:
    # try:
        instance = get_object_or_404(VehicleRequisition, id=id)
        if request.method == "POST":
            request.POST    = request.POST.copy()
            request.POST['updated_by'] = request.session.get('id')
            req_date        = request.POST.get('req_date', '')
            request.POST['req_date']   = datetime.strptime(req_date, "%d/%m/%Y") if req_date else ''
            req_duration    = request.POST.get('req_duration', '')
            if req_duration:
                durations = req_duration.split(" - ")
                request.POST['start_time']  = datetime.strptime(durations[0], "%d/%m/%Y %I:%M %p") if durations[0] else ''
                request.POST['end_time']    = datetime.strptime(durations[1], "%d/%m/%Y %I:%M %p") if durations[1] else ''
            form = VehicleRequisitionForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common_logic.form_errors(request, form)

        context = common_context()
        context['tab_name']     = "requisition"
        context['raction_name'] = "Update Requisition"
        context['raction_url']  = reverse_lazy('fa:vehicle_requisition_update', kwargs={'id':id})
        context['rform']        = VehicleRequisitionForm(instance=instance)
        context['rinstance']    = instance
        return render(request, template_name, context)
    # except : return redirect(reverse_lazy('fa:vehicle_requisition_list'))
    # else: return redirect(reverse("access_denied"))


@login
def vehicle_requisition_delete(request, id):
    instance = get_object_or_404(VehicleRequisition, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))