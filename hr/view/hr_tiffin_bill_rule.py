from hr.views import *
from hr.models import HRTiffinBillRule
from hr.forms import HRTiffinBillRuleForm
from datetime import datetime

from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()

@login
def hr_tiffin_bill_rule_list(request):
    # chk_permission = permission(request, reverse('hr:hr_tiffin_bill_rule_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        try :
            created_by = HRTiffinBillRule._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
        try :
            status  = HRTiffinBillRule._meta.get_field('status')
            status  = request.POST.get('status', 0)
            request.POST['status']  = Status.name('Inactive') if status == 0 else Status.name('Active')
        except : pass
        start_time, end_time        = request.POST.get('start_time', None), request.POST.get('end_time', None)
        request.POST['start_time']  = (datetime.strptime(start_time, "%I:%M %p")).strftime("%H:%M:%S") if start_time else ''
        request.POST['end_time']    = (datetime.strptime(end_time, "%I:%M %p")).strftime("%H:%M:%S") if end_time else ''
        form = HRTiffinBillRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/hr_tiffin_bill_rule.html"
    object_list     = HRTiffinBillRule.objects.order_by('id')
    action_url      = reverse_lazy('hr:hr_tiffin_bill_rule_list')
    action_name     = "Add HRTiffinBillRule"
    form            = HRTiffinBillRuleForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list,
                       'employee_categories' : CommonMaster.objects.filter(value_for=5) }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))

@login
def hr_tiffin_bill_rule_update(request, id):
    # chk_permission = permission(request, reverse('hr:hr_tiffin_bill_rule_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(HRTiffinBillRule, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                updated_by = HRTiffinBillRule._meta.get_field('updated_by')
                request.POST['updated_by'] = request.session.get('id')
            except : pass
            try :
                status  = HRTiffinBillRule._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            start_time, end_time        = request.POST.get('start_time', None), request.POST.get('end_time', None)
            request.POST['start_time']  = (datetime.strptime(start_time, "%I:%M %p")).strftime("%H:%M:%S") if start_time else ''
            request.POST['end_time']    = (datetime.strptime(end_time, "%I:%M %p")).strftime("%H:%M:%S") if end_time else ''
            form = HRTiffinBillRuleForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/hr_tiffin_bill_rule.html"
        action_name     = "Update HRTiffinBillRule"
        action_url      = reverse_lazy('hr:hr_tiffin_bill_rule_update', kwargs={'id':id})
        object_list     = HRTiffinBillRule.objects.order_by('id')
        form            = HRTiffinBillRuleForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 
                   'employee_categories' : CommonMaster.objects.filter(value_for=5), 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:hr_tiffin_bill_rule_list'))
    # else: return redirect(reverse("access_denied"))

@login
def hr_tiffin_bill_rule_delete(request, id):
    instance = get_object_or_404(HRTiffinBillRule, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))