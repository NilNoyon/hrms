from hr.views import *

@login
def leave_type_list(request):
    # chk_permission = permission(request, reverse('hr:leave_type_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['created_by'], status = request.session.get('id'), request.POST.get('status', 0)
        request.POST['status'] = Status.name('Inactive' if status == 0 else 'Active')
        form = HRLeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/leave/type.html"
    object_list     = HRLeaveType.objects.order_by('id')
    action_url      = reverse_lazy('hr:leave_type_list')
    action_name     = "Add Leave Type"
    form            = HRLeaveTypeForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def leave_type_update(request, id):
    # chk_permission = permission(request, reverse('hr:leave_type_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(HRLeaveType, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['updated_by'], status = request.session.get('id'), request.POST.get('status', 0)
            request.POST['status'] = Status.name('Inactive' if status == 0 else 'Active')
            form = HRLeaveTypeForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/leave/type.html"
        action_name     = "Update Leave Type"
        action_url      = reverse_lazy('hr:leave_type_update', kwargs={'id':id})
        object_list     = HRLeaveType.objects.order_by('id')
        form            = HRLeaveTypeForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:leave_type_list'))
    # else: return redirect(reverse("access_denied"))


@login
def leave_type_delete(request, id):
    instance = get_object_or_404(HRLeaveType, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))
    
@csrf_exempt
def leave_type_update_status(request):
    instance = get_object_or_404(HRLeaveType, id=request.POST.get('id'))
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return HttpResponse(instance.status)

@csrf_exempt
def leave_type_update_payable_status(request):
    instance = get_object_or_404(HRLeaveType, id=request.POST.get('id'))
    instance.payable = False if instance.payable else True
    instance.save()
    return HttpResponse('Payable Status Updated!')