import json
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.urls.base import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from general.decorators import login, permission
from general.models import *
from django.urls import reverse
from django.contrib import messages
import os.path, random, time, re
from io import StringIO 
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from general.business_logic.common_logic import Common
from datetime import datetime,timedelta
from django.db.models import F, Q, Sum
from fixedasset.views import *
import xlsxwriter 
# For Notifications
from notification.signals import notify

from tracker.models import *

@login
def export_fixed_asset(request,company,departments,item,category,subcategory,item_type,supplier,asset_user,start_date,end_date,search_text):
    chk_permission = permission(request, reverse('fa:fa_list'))
    if chk_permission and chk_permission.view_action:
        data_list = []
        fa_query = Q()
        search_text = search_text if search_text != "0" else None
        fa_list = FAAsset.objects.order_by('-id').all()
        company_short_name = company if company != "0" else None
        if company_short_name: fa_query &= Q(code__icontains=company_short_name)
        department_id = departments if departments != 0 else None
        if department_id: fa_query &= Q(department_or_cost_center_id=int(department_id))

        supplier_id = supplier if supplier != 0 else None
        if supplier_id: fa_query &= Q(supplier_id=supplier_id)

        item_type        = item_type if item_type != 0 else None
        if item_type: fa_query &= Q(classification_id=item_type)

        category_id = category if category != 0 else None
        if category_id: fa_query &= Q(item__item_master__category_id=category_id)

        subcategory_id = subcategory if subcategory != 0 else None
        if subcategory_id and not subcategory_id == 'selected': fa_query &= Q(item__item_master__sub_category_id=subcategory_id)

        item_id = item if item != 0 else None
        if item_id: fa_query &= Q(item__item_master_id=item_id)
        asset_user_id = asset_user if asset_user != 0 else None
        if asset_user_id: fa_query &= Q(asset_user_id=asset_user_id)

        start_date      = start_date if start_date != "0" else None
        end_date        = end_date if end_date != "0" else None
        if start_date or end_date:
            start_date  = datetime.strptime(start_date, "%Y-%m-%d")
            end_date    = datetime.strptime(end_date, "%Y-%m-%d")
            end_date    = end_date + timedelta(days=1)
            fa_query   &= Q(created_at__gte=start_date, created_at__lte=end_date)

        if search_text:
            search_text = search_text.strip()
            fa_query &= Q(Q(code__icontains=search_text)|
                        Q(mrir__mrir_no__icontains=search_text)|
                        Q(lc__icontains=search_text)|
                        Q(bill_of_entry_no__icontains=search_text)|
                        Q(insurer_name__icontains=search_text))
        
        fa_list    = fa_list.filter(fa_query).order_by("-id")
    
        if fa_list:
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = "attachment; filename=Fixed Asset Report.xlsx"

            workbook  = xlsxwriter.Workbook(response, {'in_memory': True})
        
            worksheet = workbook.add_worksheet()
            
            worksheet.write('A1','user_id') 
            worksheet.write('B1','company') 
            worksheet.write('C1','classification') 
            worksheet.write('D1','Category') 
            worksheet.write('E1','Sub-category')  
            worksheet.write('F1','Asset Code') 
            worksheet.write('G1','Item Code') 
            worksheet.write('H1','item_name') 
            worksheet.write('I1','technical_specification') 
            worksheet.write('J1','uom') 
            worksheet.write('K1','Serial Number') 
            worksheet.write('L1','brand') 
            worksheet.write('M1','model') 
            worksheet.write('N1','origin')  
            worksheet.write('O1','supplier') 
            worksheet.write('P1','mrir_date') 
            worksheet.write('Q1','pi_date') 
            worksheet.write('R1','lc_date') 
            worksheet.write('S1','lc') 
            worksheet.write('T1','bank') 
            worksheet.write('U1','currency') 
            worksheet.write('V1','invoice_value') 
            worksheet.write('W1','conversion_rate') 
            worksheet.write('X1','wo_price') 
            worksheet.write('Y1','tax') 
            worksheet.write('Z1','vat') 
            worksheet.write('AA1','regulatory_duty') 
            worksheet.write('AB1','bill_of_entry_no') 
            worksheet.write('AC1','bill_of_entry_date') 
            worksheet.write('AD1','total_landing_cost') 
            worksheet.write('AE1','cost_of_assets') 
            worksheet.write('AF1','product_warenty_period_year') 
            worksheet.write('AG1','last_warenty_date') 
            worksheet.write('AH1','rate_of_depreciation') 
            worksheet.write('AI1','accumulated_depreciation') 
            worksheet.write('AJ1','current_value') 
            worksheet.write('AK1','department_or_cost_center') 
            worksheet.write('AL1','payment_mode_or_acuired_mode') 
            worksheet.write('AM1','date_of_insurance') 
            worksheet.write('AN1','insurance_policy') 
            worksheet.write('AO1','insurer_name') 
            worksheet.write('AP1','insurance_expiry_date') 
            worksheet.write('AQ1','insured_value') 
            worksheet.write('AR1','claim_status') 
            worksheet.write('AS1','allocation_date') 
            worksheet.write('AT1','asset_controller_id') 
            worksheet.write('AU1','Asset Controller') 
            worksheet.write('AV1','allocated_location') 
            worksheet.write('AW1','assaign_unit/floor') 
            worksheet.write('AX1','machine_status') 
            worksheet.write('AY1','remarks') 
            worksheet.set_column(0, 18, 22) 
            worksheet.autofilter('A1:AY1')

            count = 2
            for i in fa_list:
                worksheet.write('A'+str(count), str(i.asset_user.employee_id) if i.asset_user else '')
                worksheet.write('B'+str(count), str(i.company.short_name) if i.company else '')
                worksheet.write('C'+str(count), str(i.classification) if i.classification else '')
                worksheet.write('D'+str(count), str(i.item.item_master.category) if i.item.item_master.category else '')
                worksheet.write('E'+str(count), str(i.item.item_master.sub_category.name) if i.item.item_master.sub_category else '') 
                worksheet.write('F'+str(count), str(i.code))
                worksheet.write('G'+str(count), str(i.item.item_code))
                worksheet.write('H'+str(count), str(i.item.item_master.item_name) if i.item.item_master.item_name else '')
                worksheet.write('I'+str(count), str(i.item.specification) if i.item.specification else '') 
                worksheet.write('J'+str(count), str(i.item.item_master.uom) if i.item.item_master.uom else '') 
                worksheet.write('K'+str(count), str(i.serial_no) if i.serial_no else '') 
                worksheet.write('L'+str(count), str(i.item.brand) if i.item.brand else '') 
                worksheet.write('M'+str(count), str(i.item.model) if i.item.model else '') 
                worksheet.write('N'+str(count), str(i.item.origin) if i.item.origin else '') 
                worksheet.write('O'+str(count), str(i.supplier) if i.supplier else '') 
                worksheet.write('P'+str(count), str(i.mrir_date) if i.mrir_date else '') 
                worksheet.write('Q'+str(count), str(i.pi_date) if i.pi_date else '') 
                worksheet.write('R'+str(count), str(i.lc_date) if i.lc_date else '') 
                worksheet.write('S'+str(count), str(i.lc) if i.lc else '') 
                worksheet.write('T'+str(count), str(i.bank) if i.bank else '') 
                worksheet.write('U'+str(count), str(i.currency) if i.currency else '') 
                worksheet.write('V'+str(count), str(i.asset_value) if i.asset_value else '') 
                worksheet.write('W'+str(count), str(i.conversion_rate) if i.conversion_rate else '') 
                worksheet.write('X'+str(count), str(i.wo_price) if i.wo_price else '') 
                worksheet.write('Y'+str(count), str(i.tax) if i.tax else '') 
                worksheet.write('Z'+str(count), str(i.vat) if i.vat else '') 
                worksheet.write('AA'+str(count), str(i.regulatory_duty) if i.regulatory_duty else '') 
                worksheet.write('AB'+str(count), str(i.bill_of_entry_no) if i.bill_of_entry_no else '') 
                worksheet.write('AC'+str(count), str(i.bill_of_entry_date) if i.bill_of_entry_date else '') 
                worksheet.write('AD'+str(count), str(i.total_landing_cost) if i.total_landing_cost else '') 
                worksheet.write('AE'+str(count), str(i.cost_of_assets) if i.cost_of_assets else '') 
                worksheet.write('AF'+str(count), str(i.product_warenty_period_year) if i.product_warenty_period_year else '') 
                worksheet.write('AG'+str(count), str(i.last_warenty_date) if i.last_warenty_date else '') 
                worksheet.write('AI'+str(count), str(i.rate_of_depreciation) if i.rate_of_depreciation else '') 
                worksheet.write('AJ'+str(count), str(i.accumulated_depreciation) if i.accumulated_depreciation else '') 
                worksheet.write('AK'+str(count), str(i.department_or_cost_center) if i.department_or_cost_center else '') 
                worksheet.write('AL'+str(count), str(i.payment_mode_or_acuired_mode) if i.payment_mode_or_acuired_mode else '') 
                worksheet.write('AM'+str(count), str(i.date_of_insurance) if i.date_of_insurance else '') 
                worksheet.write('AN'+str(count), str(i.insurance_policy) if i.insurance_policy else '') 
                worksheet.write('AO'+str(count), str(i.insurer_name) if i.insurer_name else '') 
                worksheet.write('AP'+str(count), str(i.insurance_expiry_date) if i.insurance_expiry_date else '') 
                worksheet.write('AQ'+str(count), str(i.insured_value) if i.insured_value else '') 
                worksheet.write('AR'+str(count), str(i.claim_status) if i.claim_status else '') 
                worksheet.write('AS'+str(count), str(i.allocation_date) if i.allocation_date else '') 
                worksheet.write('AT'+str(count), str(i.asset_controller.employee_id) if i.asset_controller else '') 
                worksheet.write('AU'+str(count), str(i.asset_controller) if i.asset_controller else '') 
                allocation = FAAssetAllocation.objects.filter(asset_user_id = i.asset_user_id).last()
                worksheet.write('AV'+str(count), str(allocation.asset_location) if allocation.asset_location else '') 
                worksheet.write('AW'+str(count), str(allocation.assign_unit_floor) if allocation.assign_unit_floor else '') 
                worksheet.write('AX'+str(count), str('') if i.remarks else '') 
                worksheet.write('AY'+str(count), str(i.remarks) if i.remarks else '') 
                count += 1
                    
            workbook.close()

            return response
        else:
            messages.warning(request, "No Data Found.")
            return redirect("/")
    else:
        return redirect('/access-denied')