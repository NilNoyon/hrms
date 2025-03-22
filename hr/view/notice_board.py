from hr.views import *


@login
def notice_board_list(request):
    # chk_permission = permission(request, reverse('hr:notice_board_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['created_by'] = request.session.get('id')
        status = request.POST.get('status', None)
        request.POST['status'] = Status.name('Active' if status and status == 'on' else 'Inactive')
        duration = request.POST.get('duration', None)
        if duration:
            durations = duration.split(" - ")
            request.POST['start_date']= datetime.strptime(durations[0], "%d/%m/%Y %I:%M %p") if durations[0] else ''
            if len(durations) == 2 :
                request.POST['end_date']  = datetime.strptime(durations[1], "%d/%m/%Y %I:%M %p") if durations[1] else ''
            else : request.POST['end_date'] = request.POST['start_date']
        form = NoticeBoardForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/notice_board.html"
    object_list     = NoticeBoard.objects.order_by('-id')
    action_url      = reverse_lazy('hr:notice_board_list')
    action_name     = "Add Notice"
    form            = NoticeBoardForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def notice_board_update(request, id):
    # chk_permission = permission(request, reverse('hr:notice_board_list'))
    # if chk_permission and chk_permission.view_action:
    # try:
        instance = get_object_or_404(NoticeBoard, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['updated_by'] = request.session.get('id')
            status = request.POST.get('status', None)
            request.POST['status'] = Status.name('Active' if status and status == 'on' else 'Inactive')
            duration = request.POST.get('duration', None)
            if duration:
                durations = duration.split(" - ")
                request.POST['start_date']= datetime.strptime(durations[0], "%d/%m/%Y %I:%M %p") if durations[0] else ''
                if len(durations) == 2 :
                    request.POST['end_date']  = datetime.strptime(durations[1], "%d/%m/%Y %I:%M %p") if durations[1] else ''
                else : request.POST['end_date'] = request.POST['start_date']
            form = NoticeBoardForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/notice_board.html"
        action_name     = "Update Notice"
        action_url      = reverse_lazy('hr:notice_board_update', kwargs={'id':id})
        object_list     = NoticeBoard.objects.order_by('-id')
        form            = NoticeBoardForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    # except : return redirect(reverse_lazy('hr:notice_board_list'))
    # else: return redirect(reverse("access_denied"))


@login
def notice_board_delete(request, id):
    instance = get_object_or_404(NoticeBoard, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))
    
@csrf_exempt
def notice_update_status(request):
    instance = get_object_or_404(NoticeBoard, id=request.POST.get('id'))
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return HttpResponse(instance.status)