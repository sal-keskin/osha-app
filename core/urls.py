from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/get_workers/', views.get_workers_json, name='get_workers_json'),
    path('api/create_profession/', views.api_create_profession, name='api_create_profession'),
    
    # Workplace
    path('workplaces/', views.workplace_list, name='workplace_list'),
    path('workplaces/new/', views.workplace_create, name='workplace_create'),
    path('workplaces/<int:pk>/edit/', views.workplace_update, name='workplace_update'),
    path('workplaces/delete/', views.workplace_bulk_delete, name='workplace_bulk_delete'),
    path('workplaces/export/', views.workplace_export, name='workplace_export'),
    path('workplaces/import/step1/', views.workplace_import, {'step': 1}, name='import_workplace_step1'),
    path('workplaces/import/step2/', views.workplace_import, {'step': 2}, name='import_workplace_step2'),
    path('workplaces/import/step3/', views.workplace_import, {'step': 3}, name='import_workplace_step3'),
    path('workplaces/import/step4/', views.workplace_import, {'step': 4}, name='import_workplace_step4'),
    
    # Worker
    path('workers/', views.worker_list, name='worker_list'),
    path('workers/new/', views.worker_create, name='worker_create'),
    path('workers/<int:pk>/edit/', views.worker_update, name='worker_update'),
    path('workers/delete/', views.worker_bulk_delete, name='worker_bulk_delete'),
    path('workers/export/', views.worker_export, name='worker_export'),
    path('workers/import/step1/', views.worker_import, {'step': 1}, name='import_worker_step1'),
    path('workers/import/step2/', views.worker_import, {'step': 2}, name='import_worker_step2'),
    path('workers/import/step3/', views.worker_import, {'step': 3}, name='import_worker_step3'),
    path('workers/import/step4/', views.worker_import, {'step': 4}, name='import_worker_step4'),

    # Educator
    path('educators/', views.educator_list, name='educator_list'),
    path('educators/new/', views.educator_create, name='educator_create'),
    path('educators/<int:pk>/edit/', views.educator_update, name='educator_update'),
    path('educators/delete/', views.educator_bulk_delete, name='educator_bulk_delete'),
    path('educators/export/', views.educator_export, name='educator_export'),
    path('educators/import/step1/', views.educator_import, {'step': 1}, name='import_educator_step1'),
    path('educators/import/step2/', views.educator_import, {'step': 2}, name='import_educator_step2'),
    path('educators/import/step3/', views.educator_import, {'step': 3}, name='import_educator_step3'),
    path('educators/import/step4/', views.educator_import, {'step': 4}, name='import_educator_step4'),

    # Professional
    path('professionals/', views.professional_list, name='professional_list'),
    path('professionals/new/', views.professional_create, name='professional_create'),
    path('professionals/<int:pk>/edit/', views.professional_update, name='professional_update'),
    path('professionals/delete/', views.professional_bulk_delete, name='professional_bulk_delete'),
    path('professionals/export/', views.professional_export, name='professional_export'),
    path('professionals/import/step1/', views.professional_import, {'step': 1}, name='import_professional_step1'),
    path('professionals/import/step2/', views.professional_import, {'step': 2}, name='import_professional_step2'),
    path('professionals/import/step3/', views.professional_import, {'step': 3}, name='import_professional_step3'),
    path('professionals/import/step4/', views.professional_import, {'step': 4}, name='import_professional_step4'),

    # Education
    path('educations/', views.education_list, name='education_list'),
    path('educations/new/', views.education_create, name='education_create'),
    path('educations/<int:pk>/edit/', views.education_update, name='education_update'),
    path('educations/delete/', views.education_bulk_delete, name='education_bulk_delete'),
    path('educations/export/', views.education_export, name='education_export'),
    path('educations/import/step1/', views.education_import, {'step': 1}, name='import_education_step1'),
    path('educations/import/step2/', views.education_import, {'step': 2}, name='import_education_step2'),
    path('educations/import/step3/', views.education_import, {'step': 3}, name='import_education_step3'),
    path('educations/import/step4/', views.education_import, {'step': 4}, name='import_education_step4'),

    # Inspection
    path('inspections/', views.inspection_list, name='inspection_list'),
    path('inspections/new/', views.inspection_create, name='inspection_create'),
    path('inspections/<int:pk>/edit/', views.inspection_update, name='inspection_update'),
    path('inspections/delete/', views.inspection_bulk_delete, name='inspection_bulk_delete'),
    path('inspections/export/', views.inspection_export, name='inspection_export'),
    path('inspections/import/step1/', views.inspection_import, {'step': 1}, name='import_inspection_step1'),
    path('inspections/import/step2/', views.inspection_import, {'step': 2}, name='import_inspection_step2'),
    path('inspections/import/step3/', views.inspection_import, {'step': 3}, name='import_inspection_step3'),
    path('inspections/import/step4/', views.inspection_import, {'step': 4}, name='import_inspection_step4'),
    
    # Examination
    path('examinations/', views.examination_list, name='examination_list'),
    path('examinations/new/', views.examination_create, name='examination_create'),
    path('examinations/<int:pk>/edit/', views.examination_update, name='examination_update'),
    path('examinations/delete/', views.examination_bulk_delete, name='examination_bulk_delete'),
    path('examinations/export/', views.examination_export, name='examination_export'),
    path('examinations/import/step1/', views.examination_import, {'step': 1}, name='import_examination_step1'),
    path('examinations/import/step2/', views.examination_import, {'step': 2}, name='import_examination_step2'),
    path('examinations/import/step3/', views.examination_import, {'step': 3}, name='import_examination_step3'),
    path('examinations/import/step4/', views.examination_import, {'step': 4}, name='import_examination_step4'),

    # Profession
    path('professions/', views.profession_list, name='profession_list'),
    path('professions/new/', views.profession_create, name='profession_create'),
    path('professions/<int:pk>/edit/', views.profession_update, name='profession_update'),
    path('professions/delete/', views.profession_bulk_delete, name='profession_bulk_delete'),
    path('professions/export/', views.profession_export, name='profession_export'),
    path('professions/import/step1/', views.profession_import, {'step': 1}, name='import_profession_step1'),
    path('professions/import/step2/', views.profession_import, {'step': 2}, name='import_profession_step2'),
    path('professions/import/step3/', views.profession_import, {'step': 3}, name='import_profession_step3'),
    path('professions/import/step4/', views.profession_import, {'step': 4}, name='import_profession_step4'),
]
