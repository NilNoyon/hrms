from multiprocessing import context
from pickle import TRUE
from re import template
from ngoasset.views import *
from django.utils import timezone
from django.db.models.query_utils import Q
from django.db.models import F,Count

@login
def get_items_from_fa(request):
    item_name = request.GET.get('q[term]', '')
    item_query = Q(item__item_master__item_name__icontains=item_name.strip())

    item_list   = Asset.objects.filter(item_query).order_by('item__item_master__item_name')
    item = [{'id': str(i.item.item_master_id), 'text': str(i.item.item_master.item_name)} for i in item_list]
    return JsonResponse({'items': list(item)}, safe=False)

@login
def get_fa_items(request):
    item_name = request.GET.get('q[term]', '')
    item_query = Q(item__item_master__item_name__icontains=item_name.strip(),asset_controller_id=int(request.session.get('id')))

    item_list   = Asset.objects.filter(item_query).order_by('item__item_master__item_name').distinct('item__item_master__item_name','item_id')
    items = [{'id': i.item_id, 'text': str(i.item.item_master.item_name)} for i in item_list]
    return JsonResponse({'items': list(items)}, safe=False)

# get asset code for Maintenance request entry
@login
def get_asset_code(request):
    item_name = request.GET.get('q[term]', '')
    company = request.GET.get('company', 0)
    item_query = Q(company_id=int(company),code__icontains=item_name.strip(),asset_controller_id=int(request.session.get('id')))
    service_running_fa = RequestDetails.objects.filter(Q(asset__code__icontains=item_name.strip())|Q(maintenance__request_no__icontains=item_name.strip())).exclude(status__title__in=['Delivered','Unrecovered']).values_list('asset_id', flat=True)
    item_list   = FAAsset.objects.filter(item_query).exclude(id__in=service_running_fa).order_by('item__item_master__item_name').annotate(text=F('code')).values('id', 'text')
    return JsonResponse({'items': list(item_list)}, safe=False)

# MR searching for assign or PR
@login
def get_mr_info(request):
    item_name = request.GET.get('q[term]', '')
    company = request.GET.get('company_id', 0)
    item_query = Q(company_id=int(company),request_no__icontains=item_name.strip())

    item_list   = MaintenanceRequest.objects.filter(item_query).exclude(status__title__in=['Solved','Delivered']).order_by('-id').annotate(text=F('request_no')).values('id', 'text')
    return JsonResponse({'items': list(item_list)}, safe=False)

# need to proceed after the items are finalized
@csrf_exempt
def get_fa_code_wise_item(request):
    item_code = request.POST.get('item_code', '')
    # getting those data from inventory business logic for code wise item
    data = ebs_bl_item.fa_code_wise_item(item_code)
    return JsonResponse(data, safe=False)

# checking requested item status 
@csrf_exempt
def check_solved_or_not(request):
    req_details = get_object_or_404(RequestDetails, id=int(request.POST.get('req_details_id', 0)))
    return JsonResponse(str(req_details.status.title), safe=False)

# get mr item info
@csrf_exempt
def get_mr_item_info(request):
    mr_id = request.POST.getlist('mr_ids[]', None)
    mr_list = MaintenanceRequest.objects.filter(id__in=mr_id)
    template_name   = 'maintenance/assign_item.html'
    return render(request, template_name, {'mr_list': mr_list})

# Generate maintenance request code
@login
def get_req_code(request, company):
    year        = time.strftime("%y", time.localtime())
    Year        = time.strftime("%Y", time.localtime())
    req_list    = MaintenanceRequest.objects.filter(company=company, created_at__year=Year).exclude(requset_branch__isnull=False).order_by('id').last()

    if req_list:
        splitted_req  = req_list.request_no.split("/")
        last_req_code = splitted_req[3]
        req_code      = "MR" + '/' + company.short_name + '/' + year + '/' + str(int(last_req_code) + 1).rjust(6, '0')
    else: req_code    = "MR" + '/' + company.short_name + '/' + year + '/' + format(1, '06d')
    return req_code

# Checking MR to MRIR
def checking_mr_to_mrir(request, id):
    details = get_object_or_404(RequestDetails, id=id)
    if details.req_details:
        count_item          = RequestDetails.objects.filter(maintenance=details.maintenance, req_details__item_id=details.req_details.item_id, req_details__spec_id=details.req_details.spec_id)
    return True

#Maintenance Request
@login
def request_list(request, tab_name='add'):
    if request.method=="POST":
        comany = Branch.objects.get(id=int(request.POST.get('branch')))
        request.POST                = request.POST.copy()
        request.POST['company']     = request.POST.get('company')
        request.POST['etd']         = datetime.strptime(request.POST.get('etd'), "%d-%b-%Y").date() if request.POST.get('etd') else ''
        request.POST['request_no']  = get_req_code(request,comany)
        request.POST['created_by']  = request.session.get('id')
        request.POST['created_at']  = timezone.now()
        request.POST['note']        = request.POST.get('notes', '')
        if request.POST.get('submition_type') == 'save': request.POST['status'] = status = Status.name('started')
        else: request.POST['status'] = status = Status.name('raised')
        request_form = MaintenanceRequestForm(request.POST)
        if request_form.is_valid(): 
            maintenance = request_form.save()
            fa_id_list  = request.POST.getlist('fa_code',[])
            fa_id       = [int(i) for i in fa_id_list]
            for f in fa_id:
                fa              = Asset.objects.get(id=f)
                problem_details = request.POST.get('problem_details[{}]'.format(f), '')
                data={
                    'maintenance'     : maintenance.id,
                    'asset'           : fa,
                    'item'            : fa.item,
                    'problem_details' : problem_details,
                    'created_by'      : request.session.get('id'),
                    'status'          : status,
                    'created_at'      : timezone.now(),
                }
                req_details_form = RequestDetailsForm(data)
                if req_details_form.is_valid(): 
                    req_details = req_details_form.save()
                    if req_details.status == Status.name('raised'):
                        ebs_bl_approval.log_entry(req_details, req_details.maintenance.request_no, req_details.created_by, '', req_details.status, None)

                else: ebs_bl_common_logic.form_errors(request, req_details_form)
            if maintenance.status == Status.name('raised'):
                ebs_bl_approval.log_entry(maintenance, maintenance.request_no, maintenance.created_by, '', maintenance.status, None)
                
                # Notification
                maintenance_user = Users.objects.filter(role__name__icontains='Maintenance',status=True)
                for n in maintenance_user:
                    n_recipient = n
                    n_sender = maintenance.created_by
                    n_description ='Maintenance request has been raised.'
                    n_action_url = reverse('fa:request_list')
                    n_model = 'MaintenanceRequest'
                    n_verb = 'Maintenance Request Raised.'
                    n_is_repeated = True
                    notify.send(sender=n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model,
                                verb=n_verb, description=n_description, is_repeated=n_is_repeated)
            messages.success(request, 'Request '+str(maintenance.status.title))
            return redirect(reverse('fa:request_list'))
        else: ebs_bl_common_logic.form_errors(request, request_form)

    context ={
                'action_name'   : "Request Entry",
                'action_url'    : reverse_lazy('fa:request_list'),
                'tab_name'      : tab_name,
                'user'          : Users.objects.get(id=request.session.get('id')),
                'dept_list'     : Departments.objects.all(),
                'company_list'  : Company.objects.order_by('name').values('id', 'name', 'short_name'),
                'categories'    : INVItemCategory.objects.order_by('name')
            }
    template_name   = 'maintenance/list.html'
    return render(request, template_name, context)

# Maintenance Request Update
@login
def request_update(request, id, tab_name=''):
    maintenance = get_object_or_404(MaintenanceRequest, id=id)
    req_details = RequestDetails.objects.filter(maintenance_id=id)
    if request.method=="POST":
        
        if request.POST.get('submition_type') == 'save': status = Status.name('started')
        else: status = Status.name('raised')
        if maintenance: 
            if request.POST.get('etd'):
                maintenance.etd = datetime.strptime(request.POST.get('etd'), "%d-%b-%Y").date() if request.POST.get('etd') else ''
            maintenance.updated_at = timezone.now()
            maintenance.note = request.POST.get('notes', '')
            maintenance.status = status
            maintenance.save()
            fa_id_list  = request.POST.getlist('fa_code',[])
            fa_id       = [int(i) for i in fa_id_list]
            for f in fa_id:
                fa              = FAAsset.objects.get(id=f)
                problem_details = request.POST.get('problem_details[{}]'.format(f), '')
                instance_details = RequestDetails.objects.filter(maintenance_id=id,asset_id=fa).first()
                if instance_details:
                    instance_details.problem_details = problem_details
                    instance_details.status = status
                    instance_details.save()
                    if instance_details.status == Status.name('raised'):
                        ebs_bl_approval.log_entry(instance_details, instance_details.maintenance.request_no, instance_details.created_by, '', instance_details.status, None)
                else:
                    data={
                        'maintenance'     : maintenance.id,
                        'asset'           : fa,
                        'item'            : fa.item,
                        'problem_details' : problem_details,
                        'created_by'      : request.session.get('id'),
                        'status'          : status,
                        'created_at'      : timezone.now(),
                    }
                    req_details_form = RequestDetailsForm(data)
                    if req_details_form.is_valid(): 
                        req_details = req_details_form.save()
                        if req_details.status == Status.name('raised'):
                            ebs_bl_approval.log_entry(req_details, req_details.maintenance.request_no, req_details.created_by, '', req_details.status, None)

                    else: ebs_bl_common_logic.form_errors(request, req_details_form)
            if maintenance.status == Status.name('raised'):
                ebs_bl_approval.log_entry(maintenance, maintenance.request_no, maintenance.created_by, '', maintenance.status, None)
                
                # Notification
                maintenance_user = Users.objects.filter(role__name__icontains='Maintenance',status=True)
                for n in maintenance_user:
                    n_recipient = n
                    n_sender = maintenance.created_by
                    n_description ='Maintenance request has been raised.'
                    n_action_url = reverse('fa:request_list')
                    n_model = 'MaintenanceRequest'
                    n_verb = 'Maintenance Request Raised.'
                    n_is_repeated = True
                    notify.send(sender=n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model,
                                verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                
            messages.success(request, 'Request '+str(maintenance.status.title))
            return redirect(reverse('fa:request_list'))
        else:
            messages.warning(request, 'Request Update Failed!.')

    context ={
                'action_name'   : "Request Update",
                'action_url'    : reverse_lazy('fa:request_update', kwargs={'id': id}),
                'tab_name'      : tab_name,
                'maintenance'   : maintenance,
                'req_details'   : req_details,
                'user'          : Users.objects.get(id=request.session.get('id')),
                'dept_list'     : Departments.objects.all(),
                'company_list'  : Company.objects.order_by('name').values('id', 'name', 'short_name'),
                'categories'    : INVItemCategory.objects.order_by('name')
            }
    template_name   = 'maintenance/list.html'
    return render(request, template_name, context)

# Maintenance Request Datatable
@csrf_exempt
def get_request_data_for_datatable(request):
    company      = request.POST.get('company', 0)
    department   = request.POST.get('department', 0)
    status       = request.POST.get('status', 0)
    item         = request.POST.get('item', 0)
    category     = request.POST.get('category', 0)
    subcategory  = request.POST.get('subcategory', 0)
    start_date   = request.POST.get('start_date', 0)
    end_date     = request.POST.get('end_date', 0)
    search_text  = request.POST.get('search_text', 0)
    start        = int(request.POST.get('start', 0))
    if request.session.get('role_text').lower() in ['maintenance']: request_list = MaintenanceRequest.objects.all()
    else: request_list = MaintenanceRequest.objects.filter(created_by_id=int(request.session.get('id')))
    fa_req_query = Q()
    if company      : fa_req_query &=Q(company=company)
    if department   : fa_req_query &=Q(requestdetails__asset__department_or_cost_center=department)
    if status       : fa_req_query &=Q(Q(status=Status.name(status))|Q(requestdetails__status=Status.name(status)))
    if item         : fa_req_query &=Q(requestdetails__asset__item_id=int(item))
    if category     : fa_req_query &=Q(requestdetails__asset__item__item_master__category=int(category))
    if subcategory and not subcategory == "selected" : fa_req_query &=Q(requestdetails__asset__item__item_master__sub_category=int(subcategory))
    
    if start_date or end_date:
        start_date      = datetime.strptime(start_date, "%Y-%m-%d")
        end_date        = datetime.strptime(end_date, "%Y-%m-%d")
        end_date        = end_date + timedelta(days=1)
        fa_req_query   &= Q(created_at__gte=start_date, created_at__lte=end_date)
    
    if search_text:
        search_text   = search_text.strip()
        fa_req_query &=Q(Q(request_no__icontains=search_text))

    request_list = request_list.filter(fa_req_query).order_by('-id')
    request_list = request_list[start:start + 20]
    data_list    = []
    for i in request_list:
        req_code    = ebs_bl_common_logic.text_url(url=reverse('fa:maintenance_view', kwargs={'id': i.id}), text=i.request_no)
        raised_by   = ebs_bl_common_logic.user_html(i.created_by, 15)
        total_items = i.requestdetails_set.all().count()
        notes       = Truncator(i.note).chars(25)
        status      = ebs_bl_common_logic.datatable_center_td(i.status.title)
        created_at  = (str(i.created_at.strftime("%d-%b-%Y").upper()) + "<br />" + (i.created_at.strftime("%I:%M %p").upper())) if i.created_at else "N/A"
        created_at  = ebs_bl_common_logic.datatable_center_td(created_at)
        eta         = str(i.etd.strftime("%d-%b-%Y").upper()) if i.etd else "N/A"
        eta         = ebs_bl_common_logic.datatable_center_td(eta)

        action = ""
        if not i.status.title == "Started":
            action      += ebs_bl_common_logic.action_html(action_url=reverse('fa:maintenance_request_status', kwargs={'id': i.id}), color_text='text-warning', icon="icon-layers", title_text="Status Details")
        if i.status.title not in ["Started","Solved","Delivered"] and request.session.get('role_text').lower() in ['maintenance']:
            action      += ebs_bl_common_logic.action_html(action_url=reverse('fa:assign_to_user', kwargs={'id': i.id}), color_text='text-success', icon="icon-arrow-right-circle", title_text="Assign or MR To PR")

        if i.created_by_id == int(request.session.get('id')) and i.status==Status.name('Started'):
            action        += ebs_bl_common_logic.action_html(action_url= reverse('fa:request_update', kwargs={'id': i.id}), color_text='text-success', icon="ti-pencil-alt")

        data = [req_code, total_items, notes, status,eta, raised_by, created_at, action]
        data_list.append(data)

    return JsonResponse(data_list, safe=False)

# Maintenance details view
@login
def maintenance_view(request, id):
    maintenance   = get_object_or_404(MaintenanceRequest, id=id)
    template_name = "maintenance/maintenance_view.html"
    context={'maintenance': maintenance }
    return render(request, template_name, context)

# Assign to Technitian or Engineer
@login
def assign_to_user(request, id):
    maintenance = get_object_or_404(MaintenanceRequest, id=id)
    if request.method=="POST":
        request_id_list      = request.POST.getlist('request_id', [])
        company              = request.POST.get('company', 0)
        assign_to            = request.POST.get('assign_to', 0)
        submission_type      = request.POST.get('submission_type', 0)
        request_id_list      = [int(i) for i in request_id_list]
        assign   = False
        
        # Assign to user 
        if submission_type == "assign":
            for m in request_id_list:
                maintenance = get_object_or_404(MaintenanceRequest, id=m)
                request_details_list = request.POST.getlist('request_details[{}]'.format(m), [])
                request_details_id   = [int(i) for i in request_details_list]
                count=0
                for chk in request_details_id:
                    check_checkboxhdn = request.POST.get('check_checkboxhdn[{}]'.format(chk), 0)
                    if int(check_checkboxhdn)==1: count +=1

                if count == len(request_details_id):
                    req_details = []
                    item_name = ""
                    for r in request_details_id:
                        notes       = request.POST.get('notes[{}]'.format(r), '')
                        req_details = RequestDetails.objects.get(id=r)

                        if req_details and int(assign_to)>0 and req_details.assign_to_id != int(assign_to):
                            req_details.remarks      = notes
                            req_details.assign_to_id = int(assign_to)
                            req_details.assign_by_id = int(request.session.get('id', 0))
                            req_details.status       = Status.name('Assigned')
                            req_details.save()
                            req_details.asset.status = Status.name('Repairing')
                            req_details.asset.save()
                            ebs_bl_approval.log_entry(req_details, req_details.maintenance.request_no, request.session.get('id'), '', req_details.status, None)

                            item_name += str(req_details.asset.item.item_master.item_name)+", "

                    # Notification
                    if len(item_name)>5:
                        n_recipient = req_details.assign_to
                        n_sender = req_details.assign_by
                        n_description = str(item_name) +' has been assigned for maintenance.'
                        n_action_url = reverse('fa:maintenance_pending')
                        n_model = 'RequestDetails'
                        n_verb = 'Assigned to Service.'
                        n_is_repeated = True
                        notify.send(sender=n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model,
                                    verb=n_verb, description=n_description, is_repeated=n_is_repeated)
                        
                        maintenance.status = Status.name('Assigned')
                        maintenance.save()
                        ebs_bl_approval.log_entry(maintenance, maintenance.request_no, request.session.get('id'), '', maintenance.status, None)
                        assign = True
                else:
                    # Request Breakdown as asign item wise 
                    parent = MaintenanceRequest.objects.filter(id=maintenance.requset_branch).first() if maintenance.requset_branch else maintenance
                    total_branch = MaintenanceRequest.objects.filter(requset_branch=parent.id).count()
                    data = {
                        'company'       : maintenance.company,
                        'etd'           : maintenance.etd,
                        'requset_branch': maintenance,
                        'request_no'    : parent.request_no + '-' + str(total_branch + 1),
                        'created_by'    : maintenance.created_by,
                        'created_at'    : maintenance.created_at,
                        'note'          : maintenance.note,
                        'status'        : Status.name('Assigned')
                    }
                    request_form = MaintenanceRequestForm(data)
                    if request_form.is_valid(): 
                        instance_maintenance = request_form.save()
                        req_details = []
                        item_name = ""
                        for r in request_details_id:
                            req_det = RequestDetails.objects.get(id=int(r))
                            notes       = request.POST.get('notes[{}]'.format(r), '')
                            check_checkboxhdn = request.POST.get('check_checkboxhdn[{}]'.format(r), 0)
                            if int(check_checkboxhdn)==1:
                                data={
                                    'maintenance'     : instance_maintenance,
                                    'asset'           : req_det.asset,
                                    'item'            : req_det.asset.item,
                                    'problem_details' : req_det.problem_details,
                                    'created_by'      : req_det.created_by,
                                    'status'          : Status.name('Assigned'),
                                    'created_at'      : req_det.created_at,
                                    'remarks'         : notes,
                                    'assign_to'    : assign_to,
                                    'assign_by'    : int(request.session.get('id', 0))
                                }
                                req_details_form = RequestDetailsForm(data)
                                if req_details_form.is_valid(): 
                                    req_details = req_details_form.save()
                                    req_details.asset.status = Status.name('Repairing')
                                    req_details.asset.save()
                                    ebs_bl_approval.log_entry(req_details, req_details.maintenance.request_no, req_details.created_by, '', Status.name('raised'), None)
                                    ebs_bl_approval.log_entry(req_details, req_details.maintenance.request_no, request.session.get('id'), '', req_details.status, None)

                                    item_name += str(req_details.asset.item.item_master.item_name)+", "
                                    req_det.delete()
                        # Notification
                        n_recipient = req_details.assign_to
                        n_sender = req_details.assign_by
                        n_description = str(item_name) +' has been assigned for maintenance.'
                        n_action_url = reverse('fa:maintenance_pending')
                        n_model = 'RequestDetails'
                        n_verb = 'Assigned to Service.'
                        n_is_repeated = True
                        notify.send(sender=n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model,
                                    verb=n_verb, description=n_description, is_repeated=n_is_repeated)

                        ebs_bl_approval.log_entry(instance_maintenance, instance_maintenance.request_no, instance_maintenance.created_by, '', Status.name('raised'), None)
                        ebs_bl_approval.log_entry(instance_maintenance, instance_maintenance.request_no, request.session.get('id'), '', instance_maintenance.status, None)
                        assign = True 

        if assign:  
            messages.success(request, 'Assigned Success')
            return redirect(reverse('fa:request_list'))

    template_name = "maintenance/assign.html"
    context={
        'maintenance': maintenance,
        'company_list'  : Company.objects.order_by('name').values('id', 'name', 'short_name'),
    }
    return render(request, template_name, context)

# Feedback from assign to 
@login
def feedback_from_assign_to(request):
    if request.method=="POST":
        request_details_id = request.POST.get('request_details_id',0)
        feedback_type      = request.POST.get('feedback_type', '')
        feedback_details   = request.POST.get('feedback_details', '')
        requset_details   = RequestDetails.objects.filter(id=int(request_details_id)).last()
        if requset_details:
            requset_details.status              = Status.name(feedback_type)
            requset_details.assign_to_feedback  = feedback_details
            requset_details.solve_by_id         = int(request.session.get('id'))
            requset_details.solve_at            = datetime.now().date()
            requset_details.save()
            if not RequestDetails.objects.filter(maintenance_id=requset_details.maintenance_id).exclude(status__title__in=['Solved','Delivered']).exists():
                instance_request = get_object_or_404(MaintenanceRequest, id=requset_details.maintenance_id)
                instance_request.status = Status.name('Solved')
                instance_request.save()
                ebs_bl_approval.log_entry(instance_request, instance_request.request_no, request.session.get('id'), '', instance_request.status, None)
            elif not RequestDetails.objects.filter(maintenance_id=requset_details.maintenance_id).exclude(status__title__in=['Not Solved']).exists():
                instance_request = get_object_or_404(MaintenanceRequest, id=requset_details.maintenance_id)
                instance_request.status = Status.name('Not Solved')
                instance_request.save()
                ebs_bl_approval.log_entry(instance_request, instance_request.request_no, request.session.get('id'), '', instance_request.status, None)

            ebs_bl_approval.log_entry(requset_details, requset_details.maintenance.request_no, requset_details.solve_by, '', requset_details.status, None)
            # Notification
            n_recipient = requset_details.assign_by
            n_sender = requset_details.assign_to
            n_description = str(requset_details.asset.item.item_master.item_name) + " Problem " +str(feedback_type)
            n_action_url = reverse('fa:maintenance_pending')
            n_model = 'RequestDetails'
            n_verb = 'Feedback From Assign To.'
            n_is_repeated = True
            notify.send(sender=n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model,
                        verb=n_verb, description=n_description, is_repeated=n_is_repeated)
        messages.success(request, 'Feedback submitted.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else: return redirect('fa:maintenance_pending')

# Delete item from request before raised
@login
def request_item_delete(request, id):
    try:
        req_details = RequestDetails.objects.filter(id=id).first()
        maintenance = MaintenanceRequest.objects.filter(id=req_details.maintenance_id).first()
        RequestDetails.objects.filter(id=id).delete()
        if not RequestDetails.objects.filter(maintenance_id=maintenance.id).exists():
            maintenance.delete()
            messages.success(request, 'Request deleted properly')
            return redirect(reverse("fa:request_list"))
        else:
            messages.success(request, 'Respective item deleted properly')
            return redirect(reverse('fa:request_update', kwargs={'id': maintenance.id}))
    except : 
        messages.warning(request, 'Request could not found')
        return redirect(reverse("fa:request_list"))

# After servicing back to requested user
@csrf_exempt
def delivery_to_user(request):
    if request.method == "POST":
        notes          = request.POST.get('delivery_notes', '')
        req_details_id = request.POST.get('req_details_id', 0)
        submission_type = request.POST.get('submission_type', '')
        # try:
        req_details = RequestDetails.objects.filter(id=int(req_details_id)).first()
        maintenance = MaintenanceRequest.objects.filter(id=req_details.maintenance_id).first()
        if req_details:
            get_status = Status.name(submission_type)
            req_details.delivery_note = notes
            req_details.status = get_status
            req_details.delivery_at = timezone.now()
            req_details.save()
            if req_details.status.title == "Delivered": req_details.asset.status = Status.name('created')
            else: req_details.asset.status = Status.name(submission_type)
            req_details.asset.save()
            ebs_bl_approval.log_entry(req_details, req_details.maintenance.request_no, req_details.assign_by, '', req_details.status, None)
            
            # Notification
            n_recipient = req_details.created_by
            n_sender = req_details.assign_by
            n_description = str(req_details.asset.item.item_master.item_name) + " Item "+str(submission_type)
            n_action_url = reverse('fa:maintenance_pending')
            n_model = 'RequestDetails'
            n_verb = 'Delivery To User.'
            n_is_repeated = True
            notify.send(sender=n_sender, recipient=n_recipient, action_url=n_action_url, model=n_model,
                        verb=n_verb, description=n_description, is_repeated=n_is_repeated)
            if not  RequestDetails.objects.filter(maintenance_id=int(maintenance.id)).exclude(status=get_status):
                maintenance.status = get_status
                maintenance.delivery_at = timezone.now()
                maintenance.save()
                ebs_bl_approval.log_entry(maintenance, maintenance.request_no, req_details.assign_by, '', maintenance.status, None)
            messages.success(request, 'Delivered properly')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        # except : messages.warning(request, 'Requisition could not found')
    else: return redirect(reverse("fa:maintenance_pending"))

# Maintenance request all item Datatable
@csrf_exempt
def maintenance_pending(request):
    if request.method=="POST":
        maintenance_pending_list   = RequestDetails.objects.filter(Q(created_by_id=int(request.session.get('id')))|Q(assign_to_id=int(request.session.get('id')))|Q(assign_by_id=int(request.session.get('id'))))
        company      = request.POST.get('company', 0)
        department   = request.POST.get('department', 0)
        status       = request.POST.get('status', 0)
        item         = request.POST.get('item', 0)
        category     = request.POST.get('category', 0)
        subcategory  = request.POST.get('subcategory', 0)
        start_date   = request.POST.get('start_date', 0)
        end_date     = request.POST.get('end_date', 0)
        search_text  = request.POST.get('search_text', 0)
        start        = int(request.POST.get('start', 0))
        fa_req_query = Q()
        if company      : fa_req_query &=Q(maintenance__company=company)
        if department   : fa_req_query &=Q(asset__department_or_cost_center=department)
        if status       : fa_req_query &=Q(status=Status.name(status))
        if item         : fa_req_query &=Q(asset__item_id=int(item))
        if category     : fa_req_query &=Q(asset__item__item_master__category=int(category))
        if subcategory and not subcategory == "selected"  : fa_req_query &=Q(asset__item__item_master__sub_category=int(subcategory))
        
        if start_date or end_date:
            start_date    = datetime.strptime(start_date, "%Y-%m-%d")
            end_date      = datetime.strptime(end_date, "%Y-%m-%d")
            end_date      = end_date + timedelta(days=1)
            fa_req_query &= Q(created_at__gte=start_date, created_at__lte=end_date)
        
        if search_text:
            search_text   = search_text.strip()
            fa_req_query &=Q(Q(maintenance__request_no__icontains=search_text)|
                            Q(asset__code__icontains=search_text))
        maintenance_pending_list = maintenance_pending_list.filter(fa_req_query).order_by('-id')
        maintenance_pending_list = maintenance_pending_list[start:start + 20]
        data_list    = []
        for i in maintenance_pending_list:
            view_url            = reverse('fa:maintenance_view', kwargs={'id': i.maintenance.id})
            fa_view_url         = reverse('fa:fa_view', kwargs={'id': i.asset_id})
            req_code            = ebs_bl_common_logic.text_url(url=view_url, text=i.maintenance.request_no)
            fa_code             = ebs_bl_common_logic.text_url(url=fa_view_url, text=i.asset.code)
            item_name           = i.asset.item.item_master.item_name
            item_spec           = sc_filters.specification(i.asset.item.item_master, i.asset.item.id).replace('<b>', '').replace('</b>', '')
            problem_details     = Truncator(i.problem_details).chars(25)
            assign_by           = ebs_bl_common_logic.user_html(i.assign_by, 15) if i.assign_by else ""
            remarks             = Truncator(i.remarks).chars(25)
            status              = ebs_bl_common_logic.datatable_center_td(i.status.title) 
            solve_by            = ebs_bl_common_logic.user_html(i.solve_by, 15) if i.solve_by else ""
            solve_at            = str(i.solve_at.strftime("%d-%b-%Y").upper()) if i.solve_at else ""
            solve_at            = ebs_bl_common_logic.datatable_center_td(solve_at)
            assign_to_feedback  = Truncator(i.assign_to_feedback).chars(25)
            action              = ""
            if not i.status.title == "Started":
                action      += ebs_bl_common_logic.action_html(action_url=reverse('fa:maintenance_request_item_status', kwargs={'id': i.id}), color_text='text-warning', icon="icon-layers", title_text="Status Details")
            if i.assign_to_id   == request.session.get('id') and i.status.title == "Assigned":
                feedback_url    = '<a href="#" data-toggle="modal" class="feedback_btn text-info" data-id="'+str(i.id)+'" data-target=".item-modal">Feedback</a>'
                action          += feedback_url
            
            if i.assign_by_id   == request.session.get('id') and not i.status.title in ["Delivered","Started","Raised"]:
                if i.status.title == "In External Service" and i.req_details:
                    req_url = i.req_details.req.get_absolute_url()
                    req_code += '<br /><a href="' + req_url + '" class="text-info" target="_blank">' + i.req_details.req.req_code + '</a>'
                    has_mrir = checking_mr_to_mrir(request, i.id)
                delivery_url    = '<a href="#" data-toggle="modal" class="delivery_btn text-info" data-id="'+str(i.id)+'" data-target=".delivery-modal" title="Delivered Or Unrecovered"><i class="ti-angle-double-right"></i></a>'
                action          += delivery_url
            
            data = [req_code, fa_code, item_name, item_spec,problem_details,assign_by, remarks, status,solve_by, solve_at, assign_to_feedback, action]
            data_list.append(data)

        return JsonResponse(data_list, safe=False)
    else:
        context ={
                'user'          : Users.objects.get(id=request.session.get('id')),
                'dept_list'     : Departments.objects.all(),
                'company_list'  : Company.objects.order_by('name').values('id', 'name', 'short_name'),
                'categories'    : INVItemCategory.objects.order_by('name')
            }
        return render(request, 'maintenance/maintenance_pending_list.html', context)

# Maintenance Report
@login
def machine_diagnostics_status(request, company,department,item,category,subcategory,status,start_date,end_date,search_text):
    if company      == 0: company = None
    if department   == 0: department = None
    if item         == 0: item = None
    if category     == 0: category = None
    if subcategory  == 0: subcategory = None
    if status       == "0": status = None
    if start_date   == "0": start_date = None
    if end_date     == "0": end_date = None
    if search_text  == "0": search_text = None
    else: search_text = search_text.replace('-','/')
    maintenance_pending_list   = RequestDetails.objects.filter(Q(created_by_id=int(request.session.get('id')))|Q(assign_to_id=int(request.session.get('id')))|Q(assign_by_id=int(request.session.get('id'))))
    fa_req_query = Q()
    if company      : fa_req_query &=Q(maintenance__company=company)
    if department   : fa_req_query &=Q(asset__department_or_cost_center=department)
    if status       : fa_req_query &=Q(status=Status.name(status))
    if item         : fa_req_query &=Q(asset__item_id=int(item))
    if category     : fa_req_query &=Q(asset__item__item_master__category=int(category))
    if subcategory  : fa_req_query &=Q(asset__item__item_master__sub_category=int(subcategory))
    
    if start_date or end_date:
        start_date    = datetime.strptime(start_date, "%Y-%m-%d")
        end_date      = datetime.strptime(end_date, "%Y-%m-%d")
        end_date      = end_date + timedelta(days=1)
        fa_req_query &= Q(created_at__gte=start_date, created_at__lte=end_date)
    
    if search_text:
        search_text   = search_text.strip()
        fa_req_query &=Q(Q(maintenance__request_no__icontains=search_text)|
                        Q(asset__code__icontains=search_text))

    maintenance_pending_list = maintenance_pending_list.filter(fa_req_query).order_by('-id')
    template_name = "maintenance/machine_diagnostic_status.html"
    user = Users.objects.filter(id=int(request.session.get('id'))).first()
    context={
        'maintenance_pending_list': maintenance_pending_list,
        'company': user.company,
    }
    pdf = render_to_pdf(template_name, context)
    if pdf: return ebs_bl_common_logic.show_pdf(request, pdf, "machine_diagnostics_status.pdf")
    return HttpResponse("Not found")

# Maintenance request approval history  
@login
def maintenance_request_status(request, id):
    maintenance = get_object_or_404(MaintenanceRequest, id=id)
    allData = dict()
    allData['statuses'] = ApprovalTable.objects.filter(reference=maintenance.request_no,ref_id=maintenance.id).order_by("approved_rejected_date")
    allData['pr_list'] = []
    
    template_name = "maintenance/status.html"
    context={
        'maintenance': maintenance, 'data' : allData
    }
    return render(request, template_name, context)


# Maintenance request approval history  
@login
def maintenance_request_item_status(request, id):
    req_details = get_object_or_404(RequestDetails, id=id)
    allData = dict()
    maintenance = get_object_or_404(MaintenanceRequest, id=req_details.maintenance_id)
    allData['statuses'] = ApprovalTable.objects.filter(reference=req_details.maintenance.request_no,ref_id=req_details.id).order_by("approved_rejected_date")  
    allData['pr_list'] = []
    
    template_name = "maintenance/status.html"
    context={
        'maintenance': maintenance, 'data' : allData
    }
    return render(request, template_name, context)

