from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from hr.models import Loan
from hr.forms import LoanForm
from django.urls import reverse_lazy
from django.contrib import messages


from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def loan_list(request):
    # chk_permission = permission(request, reverse('hr:loan_list'))
    # if chk_permission and chk_permission.view_action:
    if request.method == "POST":
        request.POST = request.POST.copy()
        try :
            created_by = Loan._meta.get_field('created_by')
            request.POST['created_by'] = request.session.get('id')
        except : pass
        try :
            status  = Loan._meta.get_field('status')
            status  = request.POST.get('status', 0)
            request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
        except : pass
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return redirect(request.META.get('HTTP_REFERER'))
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/loan.html"
    object_list     = Loan.objects.order_by('id')
    action_url      = reverse_lazy('hr:loan_list')
    action_name     = "Add Loan"
    form            = LoanForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)
    # else: return redirect(reverse("access_denied"))

@login
def loan_update(request, id):
    # chk_permission = permission(request, reverse('hr:loan_list'))
    # if chk_permission and chk_permission.view_action:
    try:
        instance = get_object_or_404(Loan, id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                updated_by = Loan._meta.get_field('updated_by')
                request.POST['updated_by'] = request.session.get('id')
            except : pass
            try :
                status  = Loan._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = LoanForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/loan.html"
        action_name     = "Update Loan"
        action_url      = reverse_lazy('hr:loan_update', kwargs={'id':id})
        object_list     = Loan.objects.order_by('id')
        form            = LoanForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:loan_list'))
    # else: return redirect(reverse("access_denied"))



@login
def loan_delete(request, id):
    instance = get_object_or_404(Loan, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))