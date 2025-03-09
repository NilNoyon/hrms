from django.urls import path
from . import views

app_name = 'desk'

urlpatterns = [
    path('', views.issue_dashboard, name='issue_dashboard'),
    path('search-issue', views.search_issue, name='search_issue'),
    path('helpdesk-report', views.helpdesk_report, name='helpdesk_report'),
    path('phonebook/', views.phonebook, name='phonebook'),

    path('get-user/', views.getUser, name='getUser'),
    path('issue-assign/', views.issue_assign, name='issue_assign'),
    path('issue-cancel/', views.issue_cancel, name='issue_cancel'),
    path('issue-resolve/', views.issue_resolve, name='issue_resolve'),
    path('issue-feedback/', views.issue_feedback, name='issue_feedback'),
    path('device-assessment-entry/', views.device_assessment_entry, name='device_assessment_entry'),
    path('device-assessment-list/', views.assessment_list, name='assessment_list'),
    path('device-assessment-approve/', views.assessment_approve, name='assessment_approve'),
    path('device-assessment-view/', views.device_assessment_view, name='device_assessment_view'),
    path('device-assessment/<int:id>/report/', views.assessment_approved_report, name='assessment_approved_report'),
    path('get-issues-for-dataTable', views.get_issues_for_dataTable, name='get_issues_for_dataTable'),
    path('generate-sr-from-desk/', views.generate_sr_from_desk, name='generate_sr_from_desk'),
]
