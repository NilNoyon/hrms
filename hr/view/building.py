from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from general.decorators import login, permission
from django.views.decorators.csrf import csrf_exempt
from general.models import Status
from hr.models import Building, Location, HRFloor
from hr.forms import BuildingForm
from django.urls import reverse, reverse_lazy
from django.db.models import Q,F
from django.contrib import messages
from general.business_logic import approval_log_logic, common_logic
ebs_bl_approval     = approval_log_logic.Approval()
ebs_bl_common       = common_logic.Common()


@login
def building_list(request):
    chk_permission = permission(request, reverse('hr:building_list'))
    if chk_permission and chk_permission.view_action:
        if request.method == "POST":
            request.POST = request.POST.copy()
            try :
                created_by = Building._meta.get_field('created_by')
                request.POST['created_by'] = request.session.get('id')
            except : pass
            try :
                status  = Building._meta.get_field('status')
                status  = request.POST.get('status', 0)
                request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
            except : pass
            form = BuildingForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Stored!")
            else : ebs_bl_common.form_errors(request, form)


        template_name   = "hr/building.html"
        locations       = Location.objects.filter(status=Status.name("Active"))
        object_list     = Building.objects.order_by('id')
        action_url      = reverse_lazy('hr:building_list')
        action_name     = "Add Building"
        form            = BuildingForm()
        context         = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'location_list':locations }
        return render(request, template_name, context)
    else: return redirect(reverse("access_denied"))


@login
def building_update(request, id):
    chk_permission = permission(request, reverse('hr:building_list'))
    if chk_permission and chk_permission.view_action:
        try:
            instance = get_object_or_404(Building, id=id)
            if request.method == "POST":

                request.POST = request.POST.copy()
                try :
                    updated_by = Building._meta.get_field('updated_by')
                    request.POST['updated_by'] = request.session.get('id')
                except : pass
                try :
                    status  = Building._meta.get_field('status')
                    status  = request.POST.get('status', 0)
                    request.POST['status'] = Status.name('Inactive') if status == 0 else Status.name('Active')
                except : pass
                form = BuildingForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Successfully Updated!")
                else : ebs_bl_common.form_errors(request, form)


            template_name   = "hr/building.html"
            action_name     = "Update Building"
            action_url      = reverse_lazy('hr:building_update', kwargs={'id':id})
            locations       = Location.objects.filter(status=Status.name("Active"))
            object_list     = Building.objects.order_by('id')
            form            = BuildingForm(instance=instance)


            context = { 'action_name':action_name, 'form':form, 'action_url':action_url, 'object_list':object_list, 'instance':instance, 'location_list':locations }
            return render(request, template_name, context)
        except : return redirect(reverse_lazy('hr:building_list'))
    else: return redirect(reverse("access_denied"))


@login
def building_delete(request, id):
    instance = get_object_or_404(Building, id=id)
    instance.delete()
    messages.success(request, "Successfully Deleted!")
    return redirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def get_company_wise_location(request):
    location_list = list(Location.objects.filter(name__icontains=request.GET.get("q[term]", "")).annotate(text=F('name')).values('id','text'))
    location_list.insert(0, {'id':"", "text":""})
    return JsonResponse({'location':location_list}, safe=False)

@csrf_exempt
def get_location_wise_building(request):
    building_list   = list(Building.objects.filter(location_id=request.POST.get('id', 0)).annotate(text=F('name')).values('id','text'))
    building_list.insert(0, '')
    return JsonResponse({'building':building_list}, safe=False)

@csrf_exempt
def get_building_wise_floor(request):
    id = request.POST.get('id', 0)
    floor_list = list(HRFloor.objects.filter(building_id=id).annotate(text=F('name')).values('id','text'))
    floor_list.insert(0, '')
    return JsonResponse({'floor':floor_list}, safe=False)

@csrf_exempt
def building_update_status(request):
    id = request.POST.get('id', 0)
    instance = get_object_or_404(Building, id=id)
    instance.status = Status.name('Active') if instance.status == Status.name('Inactive') else Status.name('Inactive')
    instance.save()
    return JsonResponse('success', safe=False)