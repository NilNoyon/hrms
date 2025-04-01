from django import forms
from .models import *

class FAItemForm(forms.ModelForm):

    class Meta:
        model = AssetItem
        fields = "__all__"

class FASubClassificationForm(forms.ModelForm):

    class Meta:
        model = AssetSubClassification
        fields = "__all__"

class FAAssetForm(forms.ModelForm):

    class Meta:
        model = Asset
        fields = '__all__'

class FAAssetAllocationForm(forms.ModelForm):

    class Meta:
        model = FAAssetAllocation
        fields = '__all__'

class FAAssetRepairForm(forms.ModelForm):

    class Meta:
        model = AssetRepair
        fields = '__all__'

class MaintenanceRequestForm(forms.ModelForm):

    class Meta:
        model = MaintenanceRequest
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(MaintenanceRequestForm, self).__init__(*args, **kwargs)
        self.fields['item_type'].required = False
        self.fields['etd'].required = False
        self.fields['req'].required = False
        self.fields['note'].required = False
        self.fields['delivery_at'].required = False

class RequestDetailsForm(forms.ModelForm):

    class Meta:
        model = RequestDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(RequestDetailsForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False
        self.fields['assign_to_feedback'].required = False
        self.fields['assign_to'].required = False
        self.fields['assign_by'].required = False
        self.fields['solve_by'].required = False
        self.fields['solve_at'].required = False
        self.fields['delivery_at'].required = False

        
# Vehicle
class VehicleForm(forms.ModelForm):
	class Meta:
		model = Vehicle
		fields = '__all__'
# VehicleAllocation
class VehicleAllocationForm(forms.ModelForm):
	class Meta:
		model = VehicleAllocation
		fields = '__all__'
		
# VehicleService
class VehicleServiceForm(forms.ModelForm):
	class Meta:
		model = VehicleService
		fields = '__all__'
		
# VehicleRequisition
class VehicleRequisitionForm(forms.ModelForm):
	class Meta:
		model = VehicleRequisition
		fields = '__all__'