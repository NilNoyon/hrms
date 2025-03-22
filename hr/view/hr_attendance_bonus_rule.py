from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from general.models import Status
from hr.models import HRAttendanceBonusRule
from hr.forms import HRAttendanceBonusRuleForm
from django.urls import reverse_lazy
from django.contrib import messages


from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def hr_attendance_bonus_rule_list(request):
    # chk_permission = permission(request, reverse('hr:hr_attendance_bonus_rule_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        try :
            created_by = HRAttendanceBonusRule._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
        try :
            status  = HRAttendanceBonusRule._meta.get_field('status')
            status  = request.POST.get('status', 0)
            request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
        except : pass
        
        form = HRAttendanceBonusRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/hr_attendance_bonus_rule.html"
    object_list     = HRAttendanceBonusRule.objects.order_by('id')
    action_url      = reverse_lazy('hr:hr_attendance_bonus_rule_list')
    action_name     = "Add HRAttendanceBonusRule"
    form            = HRAttendanceBonusRuleForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))


@login
def hr_attendance_bonus_rule_update(request, id):
    # chk_permission = permission(request, reverse('hr:hr_attendance_bonus_rule_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(HRAttendanceBonusRule, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                updated_by = HRAttendanceBonusRule._meta.get_field('updated_by')
                request.POST['updated_by'] = request.session.get('id')
            except : pass
            try :
                status  = HRAttendanceBonusRule._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = HRAttendanceBonusRuleForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/hr_attendance_bonus_rule.html"
        action_name     = "Update HRAttendanceBonusRule"
        action_url      = reverse_lazy('hr:hr_attendance_bonus_rule_update', kwargs={'id':id})
        object_list     = HRAttendanceBonusRule.objects.order_by('id')
        form            = HRAttendanceBonusRuleForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:hr_attendance_bonus_rule_list'))
    # else: return redirect(reverse("access_denied"))


@login
def hr_attendance_bonus_rule_delete(request, id):
    instance = get_object_or_404(HRAttendanceBonusRule, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))