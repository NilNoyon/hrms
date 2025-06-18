from django.shortcuts import render, redirect
from general.decorators import login, permission
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django_countries import countries
from django.utils.text import Truncator
from .models import *
from .forms import *
from django.db.models.query_utils import Q
from general.models import *
from hr.models import EmployeeDetails
from general.business_logic import common_logic,approval_log_logic
from notification.signals import notify
from general.utils import render_to_pdf
from ngoasset.templatetags import asset_filters

ebs_bl_common_logic    = common_logic.Common()
ebs_bl_approval        = approval_log_logic.Approval()

from ngoasset.models import Asset,FAAssetAllocation, AssetRepair
from ngohrms import settings
from django.urls import reverse

class QR_Text:
    def get_fa_qr_text(self, id):
        asset = Asset.objects.filter(id=id).last()
        if asset:
            asset_url = reverse('fa:fa_view', kwargs={"id": asset.id})
            technical_specification = asset_filters.specification(asset.item.item_master, asset.item.id).replace('<b>', '').replace('</b>', '')
            asset_allocation = FAAssetAllocation.objects.filter(asset=asset)
            asset_repair     = AssetRepair.objects.filter(asset=asset, repair_type=2)
            if asset_repair: technical_specification = str(technical_specification)+ str("(Upgraded)")
            asset_user_or_cost_center = (asset_allocation.last().asset_user.name+" ("+str(asset_allocation.last().asset_user.employee_id)+") " if asset_allocation.last().asset_user else (asset_allocation.last().cost_center.name if asset_allocation.last().cost_center else 'N/A')) if asset_allocation.exists() else 'N/A'
            asset_basic_info = 'User: {}\n{}\n{}\nLocation: {}\n{}{}'.format(asset_user_or_cost_center,
                                                            asset.item.item_master.item_name,
                                                            technical_specification,
                                                            asset_allocation.last().asset_location if asset_allocation.exists() else 'N/A',
                                                            settings.DOMAIN_URL,
                                                            asset_url[1:])
            return asset_basic_info
        else: return ""
 
# Vehicle Management
template_name       = "vehicle_mgt_base.html"

# ============ Vehicle Start ============ #
try: from ngoasset.view.vehicle import *
except ImportError: pass
# ============ Vehicle End ============ #


# ============ VehicleAllocation Start ============ #
try: from ngoasset.view.vehicle_allocation import *
except ImportError: pass
# ============ VehicleAllocation End ============ #
