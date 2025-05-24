from django.urls import path
from . import views
app_name = 'fa'

urlpatterns = [
	# # Vehicle
	path('', views.fixed_list, name='fixed_list'),
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