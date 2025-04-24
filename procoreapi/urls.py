from django.urls import path
from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('filtered_projects_by_stage',views.filter_projects_by_stage, name="filter_projects_by_stage"),
    path('filtered_projects_by_pm',views.filter_projects_by_pm, name="filter_projects_by_pm"),
    path('filtered_projects_by_qc',views.filter_projects_by_qc, name="filter_projects_by_qc"),
    path('searched_projects',views.search_projects, name="searched_projects"),
    path('export_to_excel',views.export_to_excel, name="export_to_excel"),
]

