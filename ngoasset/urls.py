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

]