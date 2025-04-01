from time import time
from urllib import request
from ngoasset.views import *
import pandas as pd
from ngoasset.templatetags import asset_filters
from ngohrms import settings
from datetime import datetime, timedelta
import os,re
from PIL import Image

def fixed_asset_add(request):
    if request.method == 'POST':
        request.POST = request.POST.copy()
        request.POST['code'] = 'EKCL/IT/LAPTOP/000001'
        form = FAAssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset Created Properly!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            for field in form:
                for error in field.errors:
                    messages.warning(request, "%s : %s" % (field.name, error))
    # else:
    #     messages.warning(request, 'Problem Adding this Asset')
    #     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    classifications = CommonMaster.objects.filter(value_for=14)
    currency_types = CommonMaster.objects.filter(value_for=2)
    subclassifications = AssetSubClassification.objects.all()
    departments = Departments.objects.all()
    banks = Bank.objects.all()
    users = Users.objects.filter(status=1)
    context = {
        'classifications': classifications,
        'currency_types': currency_types,
        'departments': departments,
        'users': users,
        'subclassifications': subclassifications,
        'countries': countries,
        'banks': banks
    }
    template_name = 'asset/fixed_asset.html'
    return render(request, template_name, context)

@login
def fa_list(request):
    chk_permission = permission(request, reverse('fa:fa_list'))
    if chk_permission and chk_permission.view_action:
        company_list = Branch.objects.filter(status=1,company_id=request.session.get('company_id')).order_by('short_name')
        departments  = Departments.objects.all().order_by('name')
        classification_list = CommonMaster.objects.filter(value_for=16).order_by('value')
        categories   = []
        template_name = 'asset/fixed_asset_list.html'
        context = {'company_list': company_list, 'departments': departments, 'classification_list': classification_list, 'categories': categories}
        return render(request, template_name, context)
    else:
        return redirect('/access-denied')

@login
def fa_view(request, id):
    user = get_object_or_404(Users, pk=request.session['id'])
    asset = FAAsset.objects.filter(id=id).last()
    # when scan the qr: machine name, employee/cost center, specification and location will show
    asset_basic_info = ebs_bl_fa_qr_text.get_fa_qr_text(id) #for qr text
    has_scrapped = False
    if asset.status != Status.name('Scrapped') and(request.session.get('role_text') in ["Admin", "Super Admin"] or \
        (user.secondary_role and any("fa maintainer" in s.lower() for s in user.secondary_role))) : has_scrapped = True
    allocation_query = FAAssetAllocation.objects.filter(asset_id=asset.id).order_by('-id')
    repair_query = FAAssetRepair.objects.filter(asset_id=asset.id).order_by('-id')
    last_allocation_date = allocation_query.first().created_at if allocation_query.exists() else 'n/a'
    context = {'asset': asset, 'has_scrapped': has_scrapped, 'last_allocation_date': last_allocation_date, 'asset_basic_info': asset_basic_info,
               'allocation_query': allocation_query, 'repair_query': repair_query, 'upgraded': repair_query.filter(repair_type=2)}
    template_name = 'asset/fixed_asset_view.html'
    return render(request, template_name, context)

def get_asset_code(code):
    last_fixed_asset_obj = FAAsset.objects.filter(code__icontains=code).order_by('-code')
    if last_fixed_asset_obj.first():
        splited_fa_code = last_fixed_asset_obj.first().code.split('/')
        last_fa_code = splited_fa_code[3]
        fa_code = code + str(int(last_fa_code) + 1).rjust(6,'0')
    else: fa_code = code + format(1, '06d')
    return fa_code


@csrf_exempt
def get_fa_for_datatable(request):
    data_list = []
    fa_query = Q()
    search_text = request.POST.get('search_text', '')
    start = int(request.POST.get('start', 0))
    fa_list = FAAsset.objects.order_by('-id').all()
    company_short_name = request.POST.get('company', '')
    if company_short_name: fa_query &= Q(code__icontains=company_short_name)
    department_id = request.POST.get('department', '')
    if department_id: fa_query &= Q(department_or_cost_center_id=int(department_id))

    supplier_id = request.POST.get('supplier', '')
    if supplier_id: fa_query &= Q(supplier_id=supplier_id)

    item_type        = request.POST.get('item_type', None)
    if item_type: fa_query &= Q(classification_id=item_type)

    category_id = request.POST.get('category', None)
    if category_id: fa_query &= Q(item__item_master__category_id=category_id)

    subcategory_id = request.POST.get('subcategory', None)
    if subcategory_id and not subcategory_id == 'selected': fa_query &= Q(item__item_master__sub_category_id=subcategory_id)

    item_id = request.POST.get('item', None)
    if item_id: fa_query &= Q(item__item_master_id=item_id)
    status  = request.POST.get('status', None)
    if status: fa_query &= Q(status=Status.name(status))
    asset_user_id = request.POST.get('asset_user', None)
    if asset_user_id: fa_query &= Q(asset_user_id=asset_user_id)

    start_date      = request.POST.get('start_date', '')
    end_date        = request.POST.get('end_date', '')
    if start_date or end_date:
        start_date  = datetime.strptime(start_date, "%Y-%m-%d")
        end_date    = datetime.strptime(end_date, "%Y-%m-%d")
        end_date    = end_date + timedelta(days=1)
        fa_query   &= Q(created_at__gte=start_date, created_at__lte=end_date)

    if search_text:
        search_text = search_text.strip()
        fa_query &= Q(Q(code__icontains=search_text)|
                    Q(mrir__mrir_no__icontains=search_text)|
                    Q(serial_no__icontains=search_text)|
                    Q(item__item_master__item_name__icontains=search_text)|
                    Q(item__item_code__icontains=search_text)|
                    Q(item__model__icontains=search_text)|
                    Q(item__brand__icontains=search_text)|
                    Q(item__origin__icontains=search_text)|
                    Q(item__specification__icontains=search_text)|
                    Q(lc__icontains=search_text)|
                    Q(bill_of_entry_no__icontains=search_text)|
                    Q(insurer_name__icontains=search_text))
    fa_query    = fa_list.filter(fa_query).order_by("-id")
    fa_list     = fa_query[start:start + 20]
    for fa in fa_list:
        code                  = fa.code if fa.code else 'N/A'
        item                  = fa.item.item_master.item_name if fa.item else 'N/A'
        spec                  = sc_filters.specification(fa.item.item_master, fa.item.id) if sc_filters.specification(fa.item.item_master, fa.item.id) else 'N/A'
        spec                  = Truncator(spec).chars(40) + '.....'
        asset_user            = ebs_bl_common_logic.user_html(fa.asset_user) if fa.asset_user else 'N/A'
        asset_controller      = ebs_bl_common_logic.user_html(fa.asset_controller) if fa.asset_controller else 'N/A'
        status                = ebs_bl_common_logic.datatable_center_td(fa.status.title) if fa.status else 'N/A'
        view_url              = reverse('fa:fa_view', kwargs={'id': fa.id})
        view                  = ebs_bl_common_logic.action_html(action_url=view_url, color_text='text-success', icon="ti-eye")
        update_url            = reverse('fa:fa_update', kwargs={'id': fa.id})
        edit                  = ebs_bl_common_logic.action_html(action_url=update_url, color_text='text-warning', icon="ti-pencil-alt")
        action                = view
        if fa.status and not fa.status.title == "Scrapped":
            action                += edit
        if fa.status and not fa.status.title == "Scrapped" and request.session.get('role_text') in ["Admin", "Super Admin"]:
            delete_url        = reverse('fa:fa_delete', kwargs={'id': fa.id})
            action            += '<a class="h4 m-r-10 text-danger delete_btn" href="javascript:void(0);"  data-url="' + delete_url + '" title="Delete FA"><span class="icon"><i class="ti-trash"></i></span></a>'
        data = [code, item, spec, asset_user, asset_controller, status, action]
        data_list.append(data)

    data_list = {'data_list': data_list, 'total_item': len(fa_query)}
    return JsonResponse(data_list, safe=False)


@login
def fa_update(request, id):
    chk_permission = permission(request, reverse('fa:fa_list'))
    if chk_permission and chk_permission.view_action and chk_permission.update_action:
        if request.method == 'POST':
            asset = get_object_or_404(FAAsset, pk=id)
            request.POST = request.POST.copy()
            request.POST['code'] = asset.code
            request.POST['item'] = asset.item
            request.POST['serial_no'] = request.POST.get('serial_no', '')
            request.POST['classification'] = asset.classification
            request.POST['mrir_date'] = datetime.strptime(request.POST.get('mrir_date'),
                                                        "%d-%b-%Y").date() if request.POST.get('mrir_date') else ''
            request.POST['pi_date'] = datetime.strptime(request.POST.get('pi_date'),
                                                        "%d-%b-%Y").date() if request.POST.get('pi_date') else ''
            request.POST['lc_date'] = datetime.strptime(request.POST.get('lc_date'),
                                                        "%d-%b-%Y").date() if request.POST.get('lc_date') else ''
            request.POST['bill_of_entry_date'] = datetime.strptime(request.POST.get('bill_of_entry_date'),
                                                        "%d-%b-%Y").date() if request.POST.get('bill_of_entry_date') else ''
            request.POST['date_of_insurance'] = datetime.strptime(request.POST.get('date_of_insurance'),
                                                            "%d-%b-%Y").date() if request.POST.get('date_of_insurance') else ''
            request.POST['insurance_expiry_date'] = datetime.strptime(request.POST.get('insurance_expiry_date'),
                                                                "%d-%b-%Y").date() if request.POST.get('insurance_expiry_date') else ''
            request.POST['sale_date'] = datetime.strptime(request.POST.get('sale_date'),
                                                                "%d-%b-%Y").date() if request.POST.get('sale_date') else ''
            request.POST['obsolescence_date_disposal'] = datetime.strptime(request.POST.get('obsolescence_date_disposal'),
                                                                "%d-%b-%Y").date() if request.POST.get('obsolescence_date_disposal') else ''
            request.POST['status'] = Status.name('created')
            asset_location      = request.POST.get('asset_location', '')
            migration_reasons   = request.POST.get('migration_reasons', '')
            company             = request.POST.get('company', None)
            if asset.company and company and asset.company_id != int(company):
                company_name = get_object_or_404(Company, id=int(company))
                TechSpec
                if asset.item.item_master.sub_category.short_name:
                    if asset.item.item_master.sub_category.short_name == asset.classification.value: sub_classification = asset.item.item_master.item_name
                    else: sub_classification = asset.item.item_master.sub_category.short_name
                else:
                    sub_classification = asset.item.item_master.sub_category.short_name
                request.POST['code'] = get_asset_code('{}/{}/{}/'.format(company_name.short_name, asset.classification.value, sub_classification))
            asset_form = FAAssetForm(request.POST, instance=asset)
            if asset_form.is_valid():
                asset = asset_form.save()
                last_allocation = FAAssetAllocation.objects.filter(asset_id=id).last()
                if last_allocation and (((int(request.POST.get('asset_user')) if request.POST.get('asset_user') else None) != last_allocation.asset_user_id) or (int(request.POST.get('department_or_cost_center')) != last_allocation.cost_center_id) or (asset_location != last_allocation.asset_location) or (float(request.POST.get('revalution_value')) if request.POST.get('revalution_value') else 0 != last_allocation.revalution_value)):
                    cost_center_query = Departments.objects.filter(id=request.POST.get('department_or_cost_center'))
                    allocation_data = {
                        'asset'             : asset.id,
                        'asset_user'        : asset.asset_user.id if asset.asset_user else None,
                        'cost_center'       : cost_center_query.last().id if cost_center_query.exists() else None,
                        'asset_location'    : asset_location,
                        'migration_reasons' : migration_reasons,
                        'revalution_value'  : request.POST.get('revalution_value', 0),
                        'created_by'        : request.session.get('id'),
                        'status'            : Status.name('created')
                    }
                    allocation_form = FAAssetAllocationForm(allocation_data)
                    if allocation_form.is_valid():
                        allocation_form.save()
                    else:
                        ebs_bl_common_logic.form_errors(request, allocation_form)
                else:
                    if request.POST.get('asset_user') or asset_location or request.POST.get('revalution_value'):
                        allocation_data = {
                            'asset'             : asset.id if asset else get_object_or_404(FAAsset, pk=id).id,
                            'asset_user'        : asset.asset_user.id if asset else get_object_or_404(FAAsset, pk=id).asset_user.id,
                            'asset_location'    : asset_location,
                            'migration_reasons' : migration_reasons,
                            'revalution_value'  : request.POST.get('revalution_value', 0),
                            'created_by'        : request.session.get('id'),
                            'status'            : Status.name('created')
                        }
                        allocation_form = FAAssetAllocationForm(allocation_data)
                        if allocation_form.is_valid():
                            allocation_form.save()
                        else:
                            ebs_bl_common_logic.form_errors(request, allocation_form)
                    else:
                        print('not exists')

                message = 'Fixed Asset Updated'
                messages.success(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else: ebs_bl_common_logic.form_errors(request, asset_form)

        asset = get_object_or_404(FAAsset, pk=id)
        last_allocation = FAAssetAllocation.objects.filter(asset=asset).last()
        classifications = CommonMaster.objects.filter(value_for=16).order_by('value')
        banks = Bank.objects.all().order_by('name')
        currencies = CommonMaster.objects.filter(value_for=2).order_by('value')
        departments = Departments.objects.all().order_by('name')
        last_repair = FAAssetRepair.objects.filter(asset=asset).last()

        context = {'asset': asset, 'classifications': classifications, 'banks': banks, 'currencies': currencies,
                'departments': departments, 'last_repair': last_repair, 'last_allocation': last_allocation, 'company_list': Company.objects.all()}
        template_name = 'asset/fixed_asset_update.html'
        return render(request, template_name, context)
    else:
        return redirect('/access-denied')

@login
def fa_delete(request, id):
    chk_permission = permission(request, reverse('fa:fa_list'))
    if chk_permission and chk_permission.view_action and chk_permission.delete_action:
        fa = FAAsset.objects.get(id=id)
        FAAssetRepair.objects.filter(asset=fa).delete()
        FAAssetAllocation.objects.filter(asset=fa).delete()
        ebs_bl_approval.log_entry(fa, fa.code, request.session.get('id'), '', Status.name("Deleted"), CommonMaster.name('Deleted'))
        fa.delete()
        messages.success(request, "Fixed Asset Deleted!")
        return redirect(reverse('fa:fa_list'))
    else:
        return redirect('/access-denied')

@csrf_exempt
def item_scraping(request, id):
    chk_permission = permission(request, reverse('fa:fa_list'))
    if chk_permission and chk_permission.view_action and chk_permission.delete_action:
        fa = FAAsset.objects.get(id=id)
        fa.scrapped_date = datetime.now().date()
        fa.scrapped_note = request.POST.get('notes', '')
        fa.status        = Status.name('Scrapped')
        fa.scrapped_by_id   = int(request.session.get('id'))
        fa.save()
        return JsonResponse('success', safe=False)
    else:
        return redirect('/access-denied')

@login
def fa_add_repair(request, id):
    asset = get_object_or_404(FAAsset, pk=id)
    if request.method == "POST":
        repair_type = request.POST.get('repair_type', 1)
        repair_amount = request.POST.get('repair_amount', 0)
        reason_for_repair = request.POST.get('reason_for_repair', '')
        repair_reference = request.POST.get('repair_reference', '')
        upgradation_cost = request.POST.get('upgradation_cost', 0) if repair_type == "2" else 0
        repair_date = datetime.strptime(request.POST.get('repair_date'),
                                                        "%d-%b-%Y").date() if request.POST.get('repair_date') else ''
        if repair_date or repair_amount or reason_for_repair:
            chk_repair_exist = FAAssetRepair.objects.last()
            if chk_repair_exist: file_name = str(asset.code).replace('/','_')+"_"+str(int(chk_repair_exist.id)+1)
            else: file_name = str(asset.code).replace('/','_')+"_1"

            repair_data = {
                'asset': asset.id if asset else get_object_or_404(FAAsset, pk=id).id,
                'repair_date': repair_date,
                'repair_type': repair_type,
                'repair_amount': repair_amount,
                'upgradation_cost': upgradation_cost,
                'reason_for_repair': reason_for_repair,
                'repair_reference': repair_reference,
                'created_by': request.session.get('id'),
                'status': Status.name('created')
            }
            repair_form = FAAssetRepairForm(repair_data, request.FILES)
            if repair_form.is_valid():
                repair_form.save()
                message = "Repair added"
                messages.success(request, message)
            else: ebs_bl_common_logic.form_errors(request, repair_form)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else: return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@csrf_exempt
def fa_data(request):
    fa_query = Q()
    search_text = request.POST.get('search_text', '')
    start = int(request.POST.get('start', 0))
    company_short_name = request.POST.get('company', '')
    if company_short_name: fa_query &= Q(code__icontains=company_short_name)

    supplier_id = request.POST.get('supplier', '')
    if supplier_id: fa_query &= Q(supplier_id=supplier_id)

    item_type = request.POST.get('item_type', None)
    if item_type: fa_query &= Q(classification_id=item_type)

    item_id = request.POST.get('item', None)
    if item_id: fa_query &= Q(item__item_master_id=item_id)

    asset_user_id = request.POST.get('asset_user', None)
    if asset_user_id: fa_query &= Q(asset_user_id=asset_user_id)

    start_date = request.POST.get('start_date', '')
    end_date = request.POST.get('end_date', '')
    if start_date or end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date + timedelta(days=1)
        fa_query &= Q(created_at__gte=start_date, created_at__lte=end_date)

    if search_text:
        search_text = search_text.strip()
        fa_query &= Q(Q(code__icontains=search_text) |
                      Q(mrir__mrir_no__icontains=search_text) |
                      Q(lc__icontains=search_text) |
                      Q(bill_of_entry_no__icontains=search_text) |
                      Q(insurer_name__icontains=search_text))

    fa_list = FAAsset.objects.filter(fa_query).order_by("-id")[start:start + 20]
    context         = {'items': fa_list}
    template_name   = 'asset/fa_print_table.html'
    return render(request, template_name, context)


"""
    Here I'm importing the file
    Row was checking category, sub category, uom and many for creating item master or getiing if exists
    Using that item master getting/creating the Techspec
    Using that Techspec creating the fixed asset
"""

@login
def import_fixed_asset(request):
    chk_permission = permission(request, reverse('fa:fa_upload_page'))
    if chk_permission and chk_permission.view_action and chk_permission.insert_action:
        import_file = request.FILES['import_file']
        xl = pd.read_excel(import_file, "Sheet1", engine='openpyxl')
        headers = list(xl.head())
        new_count,not_imported = 0,0
        for i in range(0, len(xl)):
            asset_user_employee_id = retrun_str_from_xls(xl['user_id'][i])
            asset_user             = Users.objects.filter(employee_id=asset_user_employee_id)

            if str(xl['Category'][i])     != 'nan': 
                category = INVItemCategory.get_name_wise_last_data(str(xl['Category'][i]))
                if not category:
                    try:
                        category, c_created        = INVItemCategory.objects.get_or_create(name=str(xl['Category'][i]))
                        if c_created:
                            category.short_name = unique_shortname(INVItemCategory.objects, str(xl['Category'][i]).upper(), 4)
                            category.save()
                    except Exception as ex:
                        messages.warning(request, ex)  
                        category = None  
            if category and str(xl['Sub-category'][i]) != 'nan': 
                sub_category = INVItemSubCategory.get_name_wise_last_data(str(xl['Sub-category'][i]))
                if not sub_category:
                    subcategory_name = (re.sub(' +', ' ',  str(xl['Sub-category'][i]))).strip()
                    if subcategory_name:
                        try:
                            sub_category, s_created     = INVItemSubCategory.objects.get_or_create(name=subcategory_name, category=category)
                            if s_created:
                                sub_category.short_name= unique_shortname(INVItemSubCategory.objects, subcategory_name.upper(), 4)
                                sub_category.save()
                        except Exception as ex:
                            messages.warning(request, ex)  
                            sub_category = None  
            uom_name = retrun_str_from_xls(xl['uom'][i])
            uom_query = INVUoM.objects.filter(short_name=uom_name)
            uom       = uom_query.last().id if uom_query.exists() else None
            if not uom:
                short_name= unique_shortname(INVUoM.objects, uom_name.lower(), 5)
                uom = INVUoM.objects.create(name=uom_name.title(), short_name=short_name)

            item_name = retrun_str_from_xls(xl['item_name'][i])
            if item_name and category and sub_category and uom:
                item_master_query = ItemMaster.objects.filter(item_name=item_name, status=True)
                if item_master_query.exists() : get_item_master = item_master_query.last()
                else : get_item_master = ItemMaster.objects.create(category=category, sub_category=sub_category, 
                                            item_name=item_name, uom_id=uom, status=True)

                # get or create tech spec item
                specification = retrun_str_from_xls(xl['technical_specification'][i])
                brand         = retrun_str_from_xls(xl['brand'][i])
                model         = retrun_str_from_xls(xl['model'][i])
                origin        = retrun_str_from_xls(xl['origin'][i])

                tech_exist    = TechSpec.objects.filter(item_master=get_item_master, specification=specification,
                                                    brand=brand, model=model, origin=origin).last()

                if not tech_exist:
                    spec_data = {
                        'item_master'   : get_item_master,
                        'item_code'     : ebs_bl_item.get_item_code(get_item_master, 'tech'),
                        'specification' : specification,
                        'brand'         : brand,
                        'model'         : model,
                        'origin'        : origin,
                        'created_by'    : request.session['id'],
                        'status'        : True
                    }
                    item = TechSpecForm(spec_data).save()
                else:
                    item = tech_exist

                # end of item and item master code

                company = retrun_str_from_xls(xl['company'][i])
                if str(xl['classification'][i]) != 'nan':
                    classification = CommonMaster.get_name_wise_last_data(str(xl['classification'][i]), 16)
                else:
                    classification = None
                if item and company and classification is not None:
                    if get_item_master.sub_category.short_name:
                        if get_item_master.sub_category.short_name == classification.value:
                            sub_classification = item.item_name
                        else:
                            sub_classification = get_item_master.sub_category.short_name
                    else:
                        sub_classification = item.item_name
                    # get fixed asset serial code
                    if xl['company'][i] != "nan":
                        company          = Company.objects.filter(short_name=str(xl['company'][i]).strip()).last()

                    bank_query       = Bank.objects.filter(name=str(xl['bank'][i]))
                    asset_controller = retrun_str_from_xls(xl['asset_controller_id'][i])
                    asset_controller = Users.objects.filter(employee_id=asset_controller)
                    
                    department_or_cost_center = Departments.get_name_wise_last_department(str(xl['department_or_cost_center'][i]))
                    data = {
                        'serial_no'        : retrun_str_from_xls(xl['Serial Number'][i]),
                        'asset_user'       : asset_user.last() if asset_user.exists() else None,
                        'item'             : item.id,
                        'classification'   : classification.id if classification else None,
                        'bank'             : bank_query.last().id if bank_query.exists() else None,
                        'company'          : company if company else None,
                        'department_or_cost_center': department_or_cost_center.id if department_or_cost_center else None,
                        'asset_controller' : asset_controller.last() if asset_controller.exists() else None,
                        'remarks'          : retrun_str_from_xls(xl['remarks'][i]),
                        'allocation_date'  : retrun_str_from_xls(str(xl['allocation_date'][i]), False, True),
                        'created_by'       : request.session.get('id'),
                        'updated_by'       : request.session.get('id'),
                        'status'           : Status.name('created')
                    }
                    asset_value = retrun_str_from_xls(xl['invoice_value'][i])
                    if asset_value:
                        currency_query                         = CommonMaster.get_name_wise_last_data(str((xl['currency'][i])).upper(), 2)
                        data['asset_value']                    = round(float(xl['invoice_value'][i]),6) if str(xl['invoice_value'][i]) != 'nan' else 0.000
                        data['currency']                       = currency_query.id if currency_query else None
                        data['conversion_rate']                = float(xl['conversion_rate'][i]) if str(xl['conversion_rate'][i]) != 'nan' else 0.000
                        data['wo_price']                       = round(float(xl['wo_price'][i]),6) if str(xl['wo_price'][i]) != 'nan' else 0.000
                        data['tax']                            = float(xl['tax'][i]) if str(xl['tax'][i]) != 'nan' else 0.000
                        data['vat']                            = float(xl['vat'][i]) if str(xl['vat'][i]) != 'nan' else 0.000
                        data['regulatory_duty']                = retrun_str_from_xls(xl['regulatory_duty'][i])
                        data['total_landing_cost']             = round(float(xl['total_landing_cost'][i]),6) if str(xl['total_landing_cost'][i]) != 'nan' else 0.000
                        data['cost_of_assets']                 = round(float(xl['cost_of_assets'][i]),6) if str(xl['cost_of_assets'][i]) != 'nan' else 0.000
                        data['rate_of_depreciation']           = float(xl['rate_of_depreciation'][i]) if str(xl['rate_of_depreciation'][i]) != 'nan' else 0.000
                        data['accumulated_depreciation']       = round(float(xl['accumulated_depreciation'][i]),6) if str(xl['accumulated_depreciation'][i]) != 'nan' else 0.000
                        data['current_value']                  = round(float(xl['current_value'][i]),6) if str(xl['current_value'][i]) != 'nan' else 0.000
              
                    supplier_query = Supplier.objects.filter(name=str(xl['supplier'][i]).upper())
                    if supplier_query.exists():
                        data['supplier']                       = supplier_query.last()
                        data['mrir_date']                      = retrun_str_from_xls(xl['mrir_date'][i], False, True)
                        data['pi_date']                        = retrun_str_from_xls(str(xl['pi_date'][i]), False, True)
                        data['lc_date']                        = retrun_str_from_xls(str(xl['lc_date'][i]), False, True)
                        data['lc']                             = retrun_str_from_xls(xl['lc'][i])
                        data['bill_of_entry_no']               = retrun_str_from_xls(xl['bill_of_entry_no'][i])
                        data['bill_of_entry_date']             = retrun_str_from_xls(str(xl['bill_of_entry_date'][i]), False, True)
                        data['last_warenty_date']              = retrun_str_from_xls(str(xl['last_warenty_date'][i]), False, True)
                        data['product_warenty_period_year']    = retrun_str_from_xls(xl['product_warenty_period_year'][i])
                        data['payment_mode_or_acuired_mode']   = retrun_str_from_xls(xl['payment_mode_or_acuired_mode'][i])

                    insurance_policy                           = retrun_str_from_xls(xl['insurance_policy'][i])
                    if insurance_policy:
                        data['insurer_name']                   = retrun_str_from_xls(xl['insurer_name'][i])
                        data['insurance_policy']               = retrun_str_from_xls(xl['insurance_policy'][i])
                        data['insurance_expiry_date']          = retrun_str_from_xls(str(xl['insurance_expiry_date'][i]), False, True)
                        data['insured_value']                  = round(float(xl['insured_value'][i]),6) if str(xl['insured_value'][i]) != 'nan' else 0.000
                        data['claim_status']                   = retrun_str_from_xls(xl['claim_status'][i])
                    fa = []
                    if "Asset Code" in headers and retrun_str_from_xls(xl['Asset Code'][i]):
                        fa = FAAsset.objects.filter(code=retrun_str_from_xls(xl['Asset Code'][i])).last()
                        if fa:
                            if company == fa.company: 
                                data['code'] = retrun_str_from_xls(fa.code)
                            else: data['code'] = get_asset_code('{}/{}/{}/'.format(retrun_str_from_xls(company.short_name), classification.value, sub_classification))
                        else: data['code'] = get_asset_code('{}/{}/{}/'.format(retrun_str_from_xls(company.short_name), classification.value, sub_classification))
                    else: 
                        data['code']        = get_asset_code('{}/{}/{}/'.format(retrun_str_from_xls(company.short_name), classification.value, sub_classification))
                    if fa: form = FAAssetForm(data, instance=fa)
                    else: form = FAAssetForm(data)
                    if form.is_valid():
                        asset = form.save()
                        chk_exist = FAAssetAllocation.objects.filter(asset_id=asset.id,asset_user=asset_user.last())
                        if not chk_exist:
                            allocation_data = {
                                'asset'             : asset.id,
                                'asset_user'        : asset.asset_user if asset.asset_user else None,
                                'cost_center'       : asset.department_or_cost_center if asset.department_or_cost_center else None,
                                'asset_location'    : retrun_str_from_xls(xl['allocated_location'][i]),
                                'assign_unit_floor' : retrun_str_from_xls(xl['assaign_unit/floor'][i]),
                                'created_by'        : request.session.get('id'),
                                'status'            : Status.name('created')
                            }
                            allocation_form = FAAssetAllocationForm(allocation_data)
                            if allocation_form.is_valid(): allocation_form.save()
                        new_count += 1
                    else:
                        not_imported += 1
                        ebs_bl_common_logic.form_errors(request, form)
                else:
                    not_imported += 1

        messages.success(request, str(new_count) + " Fixed asset imported." + str(not_imported) + " not imported")
    else:
        return redirect('/access-denied')


@login
def fa_import_page(request):
    chk_permission = permission(request, reverse('fa:fa_upload_page'))
    if chk_permission and chk_permission.view_action and chk_permission.insert_action:
        if request.method == "POST":
            import_fixed_asset(request)

        template_name = 'asset/fa_upload.html'
        return render(request, template_name)
    else:
        return redirect('/access-denied')

@login
def asset_print(request):
    chk_permission = permission(request, reverse('fa:asset_print'))
    if chk_permission and chk_permission.view_action:
        companies  = Company.objects.order_by('short_name')
        categories = INVItemCategory.objects.order_by('name')
        departments = Departments.objects.all()
        context = {'companies': companies, 'categories': categories, 'departments': departments}
        template_name = 'asset/print.html'
        return render(request, template_name, context)
    else:
        return redirect('/access-denied')

@login
def asset_search(request, company,departments,item,category,subcategory,user_field,search_box):
    asset_query = Q()
    if company     : asset_query &= Q(code__icontains=company)
    if departments : asset_query &= Q(department_or_cost_center_id=int(departments))
    if item        : asset_query &= Q(item__item_master_id=int(item))
    if category    : asset_query &= Q(item__item_master__category_id=category)
    if subcategory : asset_query &= Q(item__item_master__sub_category_id=subcategory)
    if user_field  : asset_query &= Q(asset_user_id=user_field)
    if search_box:
        search_text = search_box.strip()
        asset_query &= Q(Q(code__icontains=search_text)|
                        Q(serial_no__icontains=search_text)|
                        Q(item__item_master__item_name__icontains=search_text)|
                        Q(item__item_code__icontains=search_text)|
                        Q(item__model__icontains=search_text)|
                        Q(item__brand__icontains=search_text)|
                        Q(item__origin__icontains=search_text)|
                        Q(item__specification__icontains=search_text)|
                        Q(mrir__mrir_no__icontains=search_text)|
                        Q(lc__icontains=search_text)|
                        Q(bill_of_entry_no__icontains=search_text)|
                        Q(insurer_name__icontains=search_text))
    assets = FAAsset.objects.filter(asset_query)
    return assets

@csrf_exempt
def asset_print_list(request):
    if request.method == "POST":
        company     = request.POST.get('company', None).replace("’", "'")
        item        = request.POST.get('item', None)
        category    = request.POST.get('category', None)
        subcategory = request.POST.get('subcategory', None)
        departments = request.POST.get('department_valu', None)
        user_field  = request.POST.get('user_field', None)
        search_box  = request.POST.get('search_box', None).replace("’", "'")
    else: company,departments,item,category,subcategory,user_field,search_box == None,None,None,None,None,None,None
    assets = asset_search(request, company,departments,item,category,subcategory,user_field,search_box)
    
    new_assets = []
    for asset in assets:
        asset_basic_info = ebs_bl_fa_qr_text.get_fa_qr_text(asset.id)
        data = {
            'asset_basic_info': asset_basic_info, 
            'code': asset.code, 
            'item_name': asset.item.item_master.item_name, 
            'item_code': asset.item.item_code, 
        }
        new_assets.append(data)
    template_name = 'asset/print_list.html'
    context = {'assets': new_assets, 'total_count': assets.count()}
    return render(request, template_name, context)

@login
def asset_export(request, company,departments,item,category,subcategory,user_field,search_box):
    chk_permission = permission(request, reverse('fa:asset_print'))
    if chk_permission and chk_permission.view_action:
        if search_box != 0:
            search_box = search_box.replace('_', '/').replace('_', '/').replace('_', '/').replace('_', '/').replace('_', '/').replace("’", "'")
        else: search_box = None
        assets      = asset_search(request, company.replace("’", "'"),departments if not departments == 0 else None,item if not item == 0 else None,category if not category == 0 else None,subcategory if not subcategory == 0 else None, user_field if not user_field == 0 else None, search_box)
        new_assets = []
        for asset in assets:
            asset_basic_info = ebs_bl_fa_qr_text.get_fa_qr_text(asset.id)
            data = {
                'asset_basic_info': asset_basic_info, 
                'code': asset.code, 
            }
            new_assets.append(data)
        template_name = 'asset/export.html'
        context = {'assets': new_assets}
        return render(request, template_name, context)
    else:
        return redirect('/access-denied')