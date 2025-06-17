from django.urls import path
from . import views

app_name = 'fa'

urlpatterns = [
    # Maintenance
    # path('request-list/', views.request_list, name='request_list'),
    # path('get-items-from-fa/', views.get_items_from_fa, name='get_items_from_fa'),
    # path('get-fa-code-wise-item/', views.get_fa_code_wise_item, name='get_fa_code_wise_item'),
    # path('get-data-for-datatable/', views.get_request_data_for_datatable, name='get_request_data_for_datatable'),
    # path('get-asset-code/', views.get_asset_code, name='get_asset_code'),
    # path('maintenance-view/<int:id>/', views.maintenance_view, name='maintenance_view'),
    # path('maintenance-update/<int:id>/', views.request_update, name='request_update'),
    # path('assign-to/<int:id>/', views.assign_to_user, name='assign_to_user'),
    # path('maintenance-item-delete/<int:id>/', views.request_item_delete, name='request_item_delete'),
    # path('maintenance-pending-list/', views.maintenance_pending, name='maintenance_pending'),
    # path('feedback-from-assign-to/', views.feedback_from_assign_to, name='feedback_from_assign_to'),
    # path('delivery-to-user/', views.delivery_to_user, name='delivery_to_user'),
    # path('machine-diagnostics-status/<int:company>/<int:department>/<int:item>/<int:category>/<int:subcategory>/<str:status>/<str:start_date>/<str:end_date>/<str:search_text>/', views.machine_diagnostics_status, name='machine_diagnostics_status'),
    # path('get-fa-item/', views.get_fa_items, name='get_fa_items'),
    # path('get-mr-item/', views.get_mr_item_info, name='get_mr_item_info'),
    # path('get-mr-info/', views.get_mr_info, name='get_mr_info'),
    # path('maintenance-request-status/<int:id>/', views.maintenance_request_status, name='maintenance_request_status'),
    # path('maintenance-request-item-status/<int:id>/', views.maintenance_request_item_status, name='maintenance_request_item_status'),
    # path('checking-requested-item-status/', views.check_solved_or_not, name='check_solved_or_not'),


	# # Vehicle
	path('vehicle/', views.vehicle_list, name='vehicle_list'),
	path('vehicle/edit/<int:id>/', views.vehicle_update, name='vehicle_update'),
	path('vehicle/delete/<int:id>/', views.vehicle_delete, name='vehicle_delete'),

	# VehicleAllocation
	path('vehicle-allocation/', views.vehicle_allocation_list, name='vehicle_allocation_list'),
	path('vehicle-allocation/edit/<int:id>/', views.vehicle_allocation_update, name='vehicle_allocation_update'),
	path('vehicle-allocation/delete/<int:id>/', views.vehicle_allocation_delete, name='vehicle_allocation_delete'),

	# VehicleService
	path('vehicle-service/', views.vehicle_service_list, name='vehicle_service_list'),
	path('vehicle-service/edit/<int:id>/', views.vehicle_service_update, name='vehicle_service_update'),
	path('vehicle-service/delete/<int:id>/', views.vehicle_service_delete, name='vehicle_service_delete'),

	# VehicleRequisition
	path('vehicle-requisition/', views.vehicle_requisition_list, name='vehicle_requisition_list'),
	path('vehicle-requisition/edit/<int:id>/', views.vehicle_requisition_update, name='vehicle_requisition_update'),
	path('vehicle-requisition/delete/<int:id>/', views.vehicle_requisition_delete, name='vehicle_requisition_delete'),

]