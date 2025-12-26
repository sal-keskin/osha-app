from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Workplace
    path('workplaces/', views.workplace_list, name='workplace_list'),
    path('workplaces/new/', views.workplace_create, name='workplace_create'),
    path('workplaces/<int:pk>/edit/', views.workplace_update, name='workplace_update'),
    
    # Worker
    path('workers/', views.worker_list, name='worker_list'),
    path('workers/new/', views.worker_create, name='worker_create'),
    path('workers/<int:pk>/edit/', views.worker_update, name='worker_update'),

    # Educator
    path('educators/', views.educator_list, name='educator_list'),
    path('educators/new/', views.educator_create, name='educator_create'),
    path('educators/<int:pk>/edit/', views.educator_update, name='educator_update'),

    # Professional
    path('professionals/', views.professional_list, name='professional_list'),
    path('professionals/new/', views.professional_create, name='professional_create'),
    path('professionals/<int:pk>/edit/', views.professional_update, name='professional_update'),

    # Education
    path('educations/', views.education_list, name='education_list'),
    path('educations/new/', views.education_create, name='education_create'),
    path('educations/<int:pk>/edit/', views.education_update, name='education_update'),

    # Inspection
    path('inspections/', views.inspection_list, name='inspection_list'),
    path('inspections/new/', views.inspection_create, name='inspection_create'),
    path('inspections/<int:pk>/edit/', views.inspection_update, name='inspection_update'),
    
    # Examination
    path('examinations/', views.examination_list, name='examination_list'),
    path('examinations/new/', views.examination_create, name='examination_create'),
    path('examinations/<int:pk>/edit/', views.examination_update, name='examination_update'),
]
