from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from general.models import CommonMaster
from hr.models import HRSalarySlabMaster
from hr.forms import CommonMasterForm, HRSalarySlabForm
from django.urls import reverse_lazy
from django.contrib import messages


from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def salary_slab_list(request):
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['value_for'] = 38
        form = CommonMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/salary/salary_slab.html"
    object_list     = CommonMaster.objects.filter(value_for=38).order_by('id')
    action_url      = reverse_lazy('hr:salary_slab_list')
    action_name, form = "Add Slab/Category", CommonMasterForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)


@login
def salary_slab_update(request, id):
    try:
        instance = CommonMaster.objects.get(id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['value_for'] = 38
            form = CommonMasterForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/salary/salary_slab.html"
        action_name     = "Update Slab/Category"
        action_url      = reverse_lazy('hr:salary_slab_update', kwargs={'id':id})
        object_list     = CommonMaster.objects.filter(value_for=38).order_by('id')
        form            = CommonMasterForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:salary_slab_list'))


@login
def salary_slab_delete(request, id):
    try:
        instance = CommonMaster.objects.get(id=id)
        instance.delete()
        messages.success(request, "Successfully Deleted!")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    except : return redirect(reverse_lazy('hr:salary_slab_list'))


@login
def salary_head_list(request):
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['value_for'] = 47
        form = CommonMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
        else : ebs_bl_common.form_errors(request, form)

    template_name   = "hr/salary/salary_head.html"
    object_list     = CommonMaster.objects.filter(value_for=47).order_by('id')
    action_url      = reverse_lazy('hr:salary_head_list')
    action_name, form = "Add Salary Head", CommonMasterForm()
    context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list }
    return render(request, template_name, context)


@login
def salary_head_update(request, id):
    try:
        instance = CommonMaster.objects.get(id=id)
        if request.method == "POST":
            request.POST = request.POST.copy()
            request.POST['value_for'] = 47
            form = CommonMasterForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)

        template_name   = "hr/salary/salary_head.html"
        action_name     = "Update Salary Head"
        action_url      = reverse_lazy('hr:salary_head_update', kwargs={'id':id})
        object_list     = CommonMaster.objects.filter(value_for=47).order_by('id')
        form            = CommonMasterForm(instance=instance)

        context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance }
        return render(request, template_name, context)
    except : return redirect(reverse_lazy('hr:salary_head_list'))


@login
def salary_head_delete(request, id):
    try:
        CommonMaster.objects.get(id=id).delete()
        messages.success(request, "Successfully Deleted!")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    except : return redirect(reverse_lazy('hr:salary_head_list'))


@login
def salary_structure_list(request):
    if request.method=='POST':
        request.POST = request.POST.copy()
        if not HRSalarySlabMaster.objects.filter(slab_id = request.POST["slab"], head_id = request.POST["head"]):
            request.POST["created_by"] = int(request.session.get('id'))
            form = HRSalarySlabForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request,'Successfully Stored!')
            else : ebs_bl_common.form_errors(request, form)
        else : messages.warning(request, "This salary slab & head already exists!")
    action_name, form = "Add Salary Structure", HRSalarySlabForm()
    object_list, action_url = HRSalarySlabMaster.objects.order_by('id'), reverse_lazy('hr:salary_structure_list')
    slab_list, head_list = CommonMaster.objects.filter(value_for=38, status=1), CommonMaster.objects.filter(value_for=47, status=1)               
    context = { "action_name": action_name, 'form':form, 'action_url':action_url, "object_list":object_list, "slab_list":slab_list, "head_list":head_list }
    return render(request, 'hr/salary/salary_structure.html', context)

@login
def salary_structure_update(request, id):
    try:
        instance = get_object_or_404(HRSalarySlabMaster, id=id)
        if request.method == 'POST':
            request.POST = request.POST.copy()
            request.POST["updated_by"] = int(request.session.get('id'))
            form = HRSalarySlabForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
            else : ebs_bl_common.form_errors(request, form)
        action_name, form = "Update Salary Structure", HRSalarySlabForm(instance=instance)
        object_list, action_url = HRSalarySlabMaster.objects.order_by('id'), reverse_lazy('hr:salary_structure_update', kwargs={'id':id})
        slab_list, head_list = CommonMaster.objects.filter(value_for=38, status=1), CommonMaster.objects.filter(value_for=47, status=1)               
        context = { "action_name": action_name, 'form':form, 'action_url':action_url, "object_list":object_list, 
                   "slab_list":slab_list, "head_list":head_list, 'instance':instance }
        return render(request, 'hr/salary/salary_structure.html', context)
    except : return redirect(reverse_lazy('hr:salary_structure_list'))

@login
def salary_structure_delete(request, id):
    try:
        HRSalarySlabMaster.objects.get(id=id).delete()
        messages.success(request, "Successfully Deleted!")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    except : return redirect(reverse_lazy('hr:salary_structure_list'))
