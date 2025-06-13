from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/filtered_projects', views.filter_projects, name='filter_projects'),
    path('dashboard/searched_projects', views.search_projects, name='searched_projects'),
    path('dashboard/export_to_excel', views.export_to_excel, name='export_to_excel'),
]

