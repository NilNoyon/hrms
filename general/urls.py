from django.urls import path
from . import views

app_name = ''

urlpatterns = [
    path('', views.app_login, name='app_login'),
    path('logout/', views.app_logout, name='app_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('version/', views.version, name='version'),
    path('table/', views.table, name='table'),
    path('form', views.form, name='form'),
    path('teams/', views.teams, name='teams'),
    path('analytics-reports/', views.analytics_reports, name='analytics_reports'),

    # user management
    path('user/', views.user_index, name='user_index'),
    path('user/company/', views.company, name='company'),
    path('user/company/<int:id>/edit/', views.update_company, name='update_company'),
    path('user/company/<int:id>/delete/', views.delete_company, name='delete_company'),
    path('user/add-user/', views.addUser, name='addUser'),
    path('user/edit/<int:id>', views.user_update, name='user_edit'),
    path('user/update-status/', views.updateStatus, name='user_status'),
    path('user/change-password/', views.changePassword, name='changePassword'),
    path('user/myProfile/', views.myProfile, name='myProfile'),
    path('ajax/get-users-for-datatable/<str:status>/', views.get_users_for_dataTable, name='get_users_for_dataTable'),
    path('user/access-control-setup/', views.user_access_control_setup, name='user_access_control_setup'),
    path('user/access-control-load/', views.load_user_access_list, name='load_user_access_list'),
    path('user/access-control-list/', views.user_access_control_list, name='user_access_control_list'),
    path('user/access-control/<int:id>/delete/', views.delete_user_access_control, name='delete_user_access_control'),
    path('access-denied', views.access_denied, name='access_denied'),
    path('page-not-found', views.page_not_found, name='page_not_found'),
    path('user/password-reset', views.password_reset, name='password_reset'),
    path('forgot-password', views.forgot_password, name='forgot_password'),
    path('password/<str:token>/reset', views.forgot_password_reset, name='forgot_password_reset'),
    path('banks/', views.bank_list, name='bank_list'),
    path('bank/update/<int:id>/', views.bank_update, name='bank_update'),
    path('ajax/get/user/list/', views.get_user_list, name='get_user_list'),
    path('ajax/get/user/department/', views.get_user_department, name='get_user_department'),
    path('logged-users', views.logged_users, name='logged_users'),
    path('update-ip', views.update_ip, name='update_ip'),
    path('ajax/get-department-wise-section/', views.get_department_wise_section, name='get_department_wise_section'),
    
    path('attendance/', views.get_attendance, name='get_attendance'),

    #ajax call for dashbaord graph/chart info
    path('get-dashboard-info/', views.get_dashboard_info, name='get_dashboard_info'),

	# Departments
	path('departments/', views.departments_list, name='departments_list'),
	path('departments/edit/<int:id>/', views.departments_update, name='departments_update'),
	path('departments/delete/<int:id>/', views.departments_delete, name='departments_delete'),

	# Designations
	path('designations/', views.designations_list, name='designations_list'),
	path('designations/edit/<int:id>/', views.designations_update, name='designations_update'),
	path('designations/delete/<int:id>/', views.designations_delete, name='designations_delete'),

	# Sections
	path('sections/', views.sections_list, name='sections_list'),
	path('sections/edit/<int:id>/', views.sections_update, name='sections_update'),
	path('sections/delete/<int:id>/', views.sections_delete, name='sections_delete'),

    
]