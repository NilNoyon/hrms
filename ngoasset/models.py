from django.db import models
from django.urls.base import reverse
from django_countries.fields import CountryField
from general.models import *
import time, os, re
from functools import partial

def _update_filename(instance, filename, Path):
     Year        = time.strftime("%Y", time.localtime())
     Month       = time.strftime("%m", time.localtime())
     extension   = "." + filename.split('.')[-1]

     if instance._meta.model == FAAssetRepair : 
          counts  = FAAssetRepair.objects.filter(asset=instance.asset).count()
          code    = instance.asset.code.replace("/", '-')

     if counts   : counting = '-' + str(counts)
     else        : counting = ''

     filename    = code + counting + extension
     return os.path.join('{0}/{1}'.format(Path, Year), filename)

def upload_to(Path):
     return partial(_update_filename, Path=Path)

# Supplier
class Supplier(CoreActionWithUpdate):
     name                = models.CharField(max_length=100, blank=True, default='')
     address_1           = models.CharField(max_length=300, blank=True, default='')
     address_2           = models.CharField(max_length=300, blank=True, default='')
     email               = models.CharField(max_length=50, blank=True, default='')
     phone               = models.CharField(max_length=50, blank=True, default='')
     country             = CountryField(blank=True, null=True)
     vat_reg             = models.CharField(max_length=40, blank=True, default='')
     license_no          = models.CharField(max_length=40, blank=True, default='')
     contact_person      = models.CharField(max_length=100, blank=True, default='')
     contact_person_no   = models.CharField(max_length=50, blank=True, default='')
     vendor_type         = models.ManyToManyField(CommonMaster, related_name='vendor_type', blank=True)
     approved_by         = models.ForeignKey(Users, related_name='supplier_approved_by', on_delete=models.CASCADE, null=True, blank=True)
     status              = models.IntegerField(default=0) # 0 = Pending, 1 = Approved , 2 = Deactivate

     class Meta:
          db_table            = 'asset_suppliers'
          verbose_name        = "Asset Supplier"
          verbose_name_plural = "Asset Supplier"

     def __str__(self):
          return self.name

class SupplierBrand(CoreActionWithUpdate):
     supplier        = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True)
     brand_name      = models.CharField(max_length = 100)

     def __str__(self):
          return '%s' % (self.brand_name)

     class Meta:
          db_table            = 'asset_supplier_brands' 
          verbose_name        = "Supplier Brand"
          verbose_name_plural = "Supplier Brands"
        

class SupplierBank(models.Model):
     supplier            = models.ForeignKey(Supplier, on_delete=models.CASCADE)
     account_name1       = models.CharField(max_length=100, blank=True, default='')
     account_no1         = models.CharField(max_length=40, blank=True, default='')
     bank1               = models.ForeignKey(Bank,related_name='supplier_bank1', on_delete=models.CASCADE,null=True,blank=True)
     bank1_route_no      = models.CharField(max_length=9, null=True, blank=True)
     account_name2       = models.CharField(max_length=100, blank=True, default='')
     account_no2         = models.CharField(max_length=40, blank=True, default='')
     bank2               = models.ForeignKey(Bank,related_name='supplier_bank2',null=True,blank=True, on_delete=models.CASCADE)
     bank2_route_no      = models.CharField(max_length=9, null=True, blank=True)

     class Meta:
          db_table            = 'asset_supplier_banks'
          verbose_name        = "Supplier Bank"
          verbose_name_plural = "Supplier Banks"

class AssetClassification(models.Model):
     name = models.CharField(max_length=100, unique=True)

     class Meta:
          db_table = 'asset_classification'

     def __str__(self):
          return self.name

class AssetSubClassification(models.Model):
     name           = models.CharField(max_length=100, unique=True)
     classification = models.ForeignKey(AssetClassification, on_delete=models.CASCADE, null=True, blank=True)
     class Meta:
          db_table = 'asset_subclassification'

     def __str__(self):
          return self.name

class AssetItem(models.Model):
     name          = models.CharField(max_length=300)
     specification = models.TextField(null=True, blank=True, default='')
     brand         = models.CharField(max_length=100, null=True, blank=True, default='')
     uom           = models.ForeignKey(UoM, on_delete=models.CASCADE, null=True, blank=True)
     origin        = CountryField(null=True, blank=True)
     subclassification = models.ForeignKey(AssetSubClassification, on_delete=models.CASCADE, null=True, blank=True)

     class Meta:
          db_table = 'asset_items'

     def __str__(self):
          return self.name+' - '+self.specification

class Asset(CoreActionWithUpdate):
     code                        = models.CharField(max_length=100, unique=True)
     branch                      = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
     serial_no                   = models.CharField(max_length=100, null=True, blank=True)
     asset_user                  = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='asset_user', null=True, blank=True)
     item                        = models.ForeignKey(AssetItem, on_delete=models.CASCADE, null=True, blank=True, default=None)
     sub_classification          = models.ForeignKey(AssetSubClassification, on_delete=models.CASCADE, null=True, blank=True)
     supplier                    = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
     bank                        = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=True)
     currency                    = models.ForeignKey(CommonMaster, on_delete=models.CASCADE, related_name='currency', null=True, blank=True)
     asset_value                 = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     conversion_rate             = models.DecimalField(max_digits=15, decimal_places=6, default=1, null=True, blank=True)
     tax                         = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     vat                         = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     regulatory_duty             = models.CharField(max_length=50, null=True, blank=True, default='')
     bill_of_entry_no            = models.CharField(max_length=50, null=True, blank=True, default='')
     bill_of_entry_date          = models.DateField(null=True, blank=True)
     total_landing_cost          = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     cost_of_assets              = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     product_warenty_period_year = models.CharField(max_length=30, null=True, blank=True)
     last_warenty_date           = models.DateField(null=True, blank=True)
     rate_of_depreciation        = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     accumulated_depreciation    = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     current_value               = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     department_or_cost_center   = models.ForeignKey(Departments, on_delete=models.CASCADE, null=True, blank=True, default=None)
     asset_controller            = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='asset_controller', null=True, blank=True)
     remarks                     = models.CharField(max_length=200, null=True, blank=True, default='')
     payment_mode_or_acuired_mode= models.CharField(max_length=100, null=True, blank=True, default='')
     date_of_insurance           = models.DateField(null=True, blank=True)
     insurance_policy            = models.TextField(null=True, blank=True, default='')
     insurer_name                = models.CharField(max_length=100, null=True, blank=True, default='')
     insurance_expiry_date       = models.DateField(null=True, blank=True)
     insured_value               = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     claim_status                = models.CharField(max_length=200, null=True, blank=True, default='')
     allocation_date             = models.DateField(null=True, blank=True)
     sale_date                   = models.DateField(null=True, blank=True)
     scrapped_date               = models.DateField(null=True, blank=True)
     scrapped_note               = models.TextField(null=True, blank=True)
     others_accessories          = models.TextField(null=True, blank=True)
     scrapped_by                 = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='scrapped_by', null=True, blank=True)
     sale_amount                 = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
     obsolescence_date_disposal  = models.DateField(null=True, blank=True)

     class Meta:
          db_table = 'fa_assets'

     def __str__(self):
          return self.code

class AssetRepair(CoreAction):
     asset               = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)
     repair_date         = models.DateField(null=True, blank=True)
     repair_amount       = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
     reason_for_repair   = models.CharField(max_length=200, null=True, blank=True, default='')
     repair_reference    = models.CharField(max_length=200, null=True, blank=True, default='')
     attachment          = models.FileField(upload_to=upload_to("FAR"), max_length = 100, blank=True, null=True)
     repair_types        = (
                              (1, 'Repair'), #this is use for Shipment Mode in MnM order entry 
                              (2, 'Upgrade'), #this is use for Currency Type in MnM order entry 
                         )
     repair_type         = models.IntegerField(null=True, blank=True, choices=repair_types, default=1)
     upgradation_cost    = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)

     class Meta:
          db_table = 'asset_repair'

     class Meta:
          db_table = 'asset_repair'

class FAAssetAllocation(CoreActionWithUpdate):
     asset              = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)
     asset_user         = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, blank=True)
     cost_center        = models.ForeignKey(Departments, on_delete=models.CASCADE, null=True, blank=True, default=None)
     asset_location     = models.TextField(null=True, blank=True)
     revalution_value   = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
     assign_unit_floor  = models.CharField(max_length=100, null=True, blank=True)
     migration_reasons  = models.TextField(null=True, blank=True)

     class Meta:
          db_table = 'asset_allocation'

class MaintenanceRequest(CoreAction):
     request_no     = models.CharField(max_length=100, unique=True)
     branch         = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
     etd            = models.DateField(auto_now=False, null=True, blank=True)
     item_types     =((0,'Fixed Asset'),(1,'Others'))
     item_type      = models.IntegerField(null=True, blank=True, choices=item_types, default=0)
     requset_branch = models.ForeignKey('self',on_delete=models.CASCADE,related_name='maintenance_requset_branch', null=True, blank=True)
     note           = models.TextField()
     updated_at     = models.DateTimeField(auto_now=True, null=True, blank=True)
     delivery_at    = models.DateTimeField(null=True, blank=True)

     def __str__(self):
          return str(self.request_no)

     class Meta:
          db_table            = 'asset_maintenance_request'
          verbose_name        = "Asset Maintenance Request"
          verbose_name_plural = "Asset Maintenance Requests"

     def get_absolute_url(self):
          return reverse("fa:maintenance_view", kwargs={"id": self.pk})
    

class RequestDetails(CoreAction):
     maintenance       = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, null=True, blank=True)
     asset             = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)
     item              = models.ForeignKey(AssetItem, on_delete=models.CASCADE, null=True, blank=True, default=None)
     remarks           = models.TextField(null=True, blank=True)
     problem_details   = models.TextField(null=True, blank=True)
     assign_to_feedback = models.TextField(null=True, blank=True)
     delivery_note     = models.TextField(null=True, blank=True)
     assign_to         = models.ForeignKey(Users, related_name="%(class)s_assign_to", related_query_name="%(class)s_assign_to", 
                                   on_delete=models.CASCADE, null=True, blank=True, default=None)
     assign_by         = models.ForeignKey('general.Users', related_name="%(class)s_assign_by", related_query_name="%(class)s_assign_by", 
                                   on_delete=models.CASCADE, null=True, blank=True, default=None)
     solve_by          = models.ForeignKey('general.Users', related_name="%(class)s_solve_by", related_query_name="%(class)s_solve_by", 
                                   on_delete=models.CASCADE, null=True, blank=True, default=None)
     solve_at          = models.DateField(null=True, blank=True, default=None)
     delivery_at       = models.DateTimeField(null=True, blank=True)

     def __str__(self):
          return str(self.maintenance.request_no)+" - "+ str(self.asset.item.item_master.item_name) if self.asset else "N/A"

     class Meta:
          db_table            = 'asset_request_details'
          verbose_name        = "Asset Request Details"
          verbose_name_plural = "Asset Requests Details"


# Vehicle
class Vehicle(CoreActionWithUpdate):
     vehicle_types   = (
          ('Rent', 'Rent'),
          ('Own', 'Own'),
     )
     categories      = (
          ('Private', 'Private'),
          ('Official', 'Official'),
     )
     vehicle_type    = models.CharField(max_length=10, choices=vehicle_types)
     category        = models.CharField(max_length=15, choices=categories)
     name            = models.CharField(max_length=100, default='', null=True, blank=True)
     model           = models.CharField(max_length=30, default='', null=True, blank=True)
     year            = models.IntegerField(default=0, null=True, blank=True)
     reg_no          = models.CharField(max_length=30, default='', null=True, blank=True)
     num_of_seats    = models.IntegerField(default=1) 
     reg_exp_date    = models.DateField(auto_now=False, null=True, blank=True)
     fitness_exp_date= models.DateField(auto_now=False, null=True, blank=True)
     rent_date       = models.DateField(auto_now=False, null=True, blank=True)
     actual_cost     = models.IntegerField(default=0, null=True, blank=True)
     net_worth       = models.IntegerField(default=0, null=True, blank=True)
     driver_assigned_date = models.DateTimeField(auto_now=False, null=True, blank=True)
     driver_name     = models.CharField(max_length=100, default='', null=True, blank=True)
     driver_employee_id = models.CharField(max_length = 15, default='', null=True, blank=True)
     remarks         = models.TextField(default='', null=True, blank=True)

     class Meta:
          db_table            = 'vmgt_vehicles'
          verbose_name        = 'Vehicle'
          verbose_name_plural = 'Vehicles'
          indexes = [
               models.Index(fields=['name', 'model', 'reg_no']),
          ]

     def __str__(self):
          return (self.name if self.name else '') + ((str(" - ") + self.model) if self.model else '') + ((str(" - ") + self.reg_no) if self.reg_no else '')

class VehicleAllocation(CoreActionWithUpdate):
     assigned_to     = models.ForeignKey(Users, on_delete=models.CASCADE) 
     vehicle         = models.ForeignKey(Vehicle, on_delete=models.CASCADE) 
     assigned_date   = models.DateTimeField(auto_now=False, null=True, blank=True)
     exp_date        = models.DateTimeField(auto_now=False, null=True, blank=True)
     remarks         = models.TextField(default='', null=True, blank=True)
     remarks         = models.TextField(default='', null=True, blank=True)

     class Meta:
          db_table            = 'vmgt_vehicle_allocations'
          verbose_name        = 'Vehicle Allocation'
          verbose_name_plural = 'Vehicle Allocations'

     def __str__(self):
          return (self.assigned_to.name if self.assigned_to else '') + str(" - ") + (self.vehicle.name if self.vehicle else '')

class VehicleService(CoreActionWithUpdate):
     vehicle         = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True) 
     provider        = models.CharField(max_length=100, default='', null=True, blank=True)
     details         = models.CharField(max_length=200, default='', null=True, blank=True)
     location        = models.CharField(max_length=150, default='', null=True, blank=True)
     repair_cost     = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, default=0)
     repair_date     = models.DateTimeField(auto_now=False, null=True, blank=True)
     remarks         = models.TextField(default='', null=True, blank=True)

     class Meta:
          db_table            = 'vmgt_vehicle_services'
          verbose_name        = 'Vehicle Service'
          verbose_name_plural = 'Vehicle Services'

     def __str__(self):
          return self.provider

class VehicleRequisition(CoreActionWithUpdate):
     route_types   = (
          ('One way', 'One way'),
          ('Two way', 'Two way'),
     )
     vehicle         = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True) 
     visiting_place  = models.CharField(max_length=150, default='', null=True, blank=True)
     start_from      = models.CharField(max_length=150, default='', null=True, blank=True)
     route_type      = models.CharField(max_length=10, choices=route_types)
     num_of_persons  = models.IntegerField(default=1) 
     req_date        = models.DateTimeField(auto_now=False, blank=True, null=True)
     start_time      = models.DateTimeField(auto_now=False, blank=True, null=True)
     end_time        = models.DateTimeField(auto_now=False, blank=True, null=True)
     remarks         = models.TextField(default='', null=True, blank=True)

     class Meta:
          db_table            = 'vmgt_vehicle_requisitions'
          verbose_name        = 'Vehicle Requisition'
          verbose_name_plural = 'Vehicle Requisitions'
