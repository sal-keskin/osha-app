from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/get_workers/', views.get_workers_json, name='get_workers_json'),
    path('api/get_facilities/', views.api_get_facilities, name='get_facilities_json'),
    path('api/search_nace/', views.api_search_nace, name='api_search_nace'),
    path('api/create_profession/', views.api_create_profession, name='api_create_profession'),
    path('api/statistics/', views.api_get_statistics, name='api_get_statistics'),
    path('statistics/', views.statistics_view, name='statistics'),
    
    # Workplace
    path('workplaces/', views.workplace_list, name='workplace_list'),
    path('workplaces/new/', views.workplace_create, name='workplace_create'),
    path('workplaces/<int:pk>/', views.workplace_detail, name='workplace_detail'),
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
    path('educations/certificate/', views.education_certificate_download, name='education_certificate_download'),
    path('educations/certificate/docx/', views.education_certificate_word, name='education_certificate_word'),
    path('educations/<int:pk>/participation-form/', views.education_participation_form, name='education_participation_form'),

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
    path('examinations/<int:pk>/update-note/', views.update_examination_note, name='update_examination_note'),
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

    # Facility
    path('facilities/', views.facility_list, name='facility_list'),
    path('facilities/new/', views.facility_create, name='facility_create'),
    path('facilities/<int:pk>/', views.facility_detail, name='facility_detail'),
    path('facilities/<int:pk>/settings/', views.facility_update, name='facility_update'),
    path('facilities/delete/', views.facility_bulk_delete, name='facility_bulk_delete'),
    path('facilities/import/step1/', views.facility_import, {'step': 1}, name='import_facility_step1'),
    path('facilities/import/step2/', views.facility_import, {'step': 2}, name='import_facility_step2'),
    path('facilities/import/step3/', views.facility_import, {'step': 3}, name='import_facility_step3'),
    path('facilities/import/step4/', views.facility_import, {'step': 4}, name='import_facility_step4'),
    path('facilities/export/', views.facility_export, name='facility_export'),

    # Assessments
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/<int:pk>/delete/', views.assessment_delete, name='assessment_delete'),
    path('assessments/bulk-delete/', views.assessment_bulk_delete, name='assessment_bulk_delete'),
    path('facilities/<int:facility_id>/assessments/new/', views.assessment_session_create, name='assessment_session_create'),
    path('assessments/<int:pk>/run/', views.assessment_session_run, name='assessment_session_run'),
    path('assessments/<int:pk>/run-fast/', views.assessment_fast_run, name='assessment_fast_run'),
    path('assessments/<int:session_pk>/save-answer/', views.assessment_answer_save, name='assessment_answer_save'),
    
    # Fast Track API
    path('api/risk-library/', views.api_get_risk_library, name='api_risk_library'),
    path('api/risk-library/categories/', views.api_get_risk_categories, name='api_risk_categories'),
    path('assessments/<int:session_pk>/add-library-risk/', views.api_add_library_risk, name='api_add_library_risk'),
    path('assessments/<int:session_pk>/update-fast-risk/<int:risk_pk>/', views.api_update_fast_risk, name='api_update_fast_risk'),
    path('assessments/<int:session_pk>/delete-fast-risk/<int:risk_pk>/', views.api_delete_fast_risk, name='api_delete_fast_risk'),
    path('assessments/<int:session_pk>/risk/<int:risk_pk>/control-records/', views.api_get_control_records, name='api_get_control_records'),
    path('assessments/<int:session_pk>/risk/<int:risk_pk>/control-records/add/', views.api_create_control_record, name='api_create_control_record'),
    
    # Custom Risks
    path('assessments/<int:session_pk>/custom-risks/', views.custom_risk_list, name='custom_risk_list'),
    path('assessments/<int:session_pk>/custom-risks/new/', views.custom_risk_create, name='custom_risk_create'),
    path('assessments/<int:session_pk>/custom-risks/<int:pk>/edit/', views.custom_risk_update, name='custom_risk_update'),
    path('assessments/<int:session_pk>/custom-risks/<int:pk>/delete/', views.custom_risk_delete, name='custom_risk_delete'),

    # Action Plan
    path('assessments/<int:session_pk>/action-plan/', views.action_plan_list, name='action_plan_list'),
    path('assessments/<int:session_pk>/action-plan/intro/', views.action_plan_intro, name='action_plan_intro'),
    path('assessments/<int:session_pk>/action-plan/<str:risk_type>/<int:risk_id>/', views.action_plan_edit, name='action_plan_edit'),
    path('assessments/<int:session_pk>/action-plan/<str:risk_type>/<int:risk_id>/priority/', views.action_plan_priority_update, name='action_plan_priority_update'),
    path('assessments/<int:session_pk>/action-plan/<str:risk_type>/<int:risk_id>/measure/add/', views.measure_add, name='measure_add'),
    path('assessments/<int:session_pk>/action-plan/measure/<int:measure_id>/update/', views.measure_update, name='measure_update'),
    path('assessments/<int:session_pk>/action-plan/measure/<int:measure_id>/delete/', views.measure_delete, name='measure_delete'),

    # Status & Reporting
    path('assessments/<int:session_pk>/status/', views.assessment_status, name='assessment_status'),
    path('assessments/<int:session_pk>/report/', views.assessment_report, name='assessment_report'),
    path('assessments/<int:session_pk>/team/', views.assessment_team, name='assessment_team'),
    path('assessments/<int:session_pk>/export/excel/', views.export_action_plan_excel, name='export_action_plan_excel'),
    path('assessments/<int:session_pk>/export/word/', views.export_report_word, name='export_report_word'),
    path('assessments/<int:session_pk>/export/pdf/', views.export_report_pdf, name='export_report_pdf'),
    path('assessments/<int:session_pk>/export/checklist/', views.export_full_checklist_pdf, name='export_full_checklist_pdf'),

    # Risk Tools
    path('risk-tools/', views.risk_tool_list, name='risk_tool_list'),
    path('risk-tools/new/', views.risk_tool_create, name='risk_tool_create'),
    path('risk-tools/<int:pk>/edit/', views.risk_tool_update, name='risk_tool_update'),
    path('risk-tools/<int:pk>/delete/', views.risk_tool_delete, name='risk_tool_delete'),
    path('risk-tools/import/', views.risk_tool_import, name='risk_tool_import'),
    path('risk-tools/template/', views.risk_tool_template_download, name='risk_tool_template'),

    # Settings & Users
    path('settings/', views.settings_view, name='settings'),
    path('settings/certificate/', views.certificate_settings_view, name='certificate_settings'),
    path('settings/users/', views.user_list, name='user_list'),
    path('settings/users/new/', views.user_create, name='user_create'),
    path('settings/users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('settings/users/delete/', views.user_bulk_delete, name='user_bulk_delete'),
    path('settings/users/<int:pk>/update_profile/', views.user_update_profile_ajax, name='user_update_profile_ajax'),
    path('settings/assignments/create/', views.workplace_assignment_create, name='workplace_assignment_create'),
    path('settings/assignments/<int:pk>/update/', views.api_update_assignment, name='api_update_assignment'),
    path('settings/assignments/<int:pk>/delete/', views.api_delete_assignment, name='api_delete_assignment'),
    path('settings/assignments/<int:pk>/revoke/', views.workplace_assignment_revoke, name='workplace_assignment_revoke'),
    path('settings/logs/', views.log_list, name='log_list'),

    # Public Safety Forum (NO login required)
    path('voice/<uuid:facility_uuid>/', views.public_safety_forum, name='public_safety_forum'),
    path('voice/<uuid:facility_uuid>/submit/', views.public_safety_submit, name='public_safety_submit'),
    path('voice/<uuid:facility_uuid>/vote/<int:poll_id>/', views.public_poll_vote, name='public_poll_vote'),

    # Facility QR Code & Engagements (login required)
    path('facilities/<int:pk>/qr-code/', views.facility_qr_code, name='facility_qr_code'),
    path('facilities/<int:pk>/engagements/', views.facility_engagements, name='facility_engagements'),
    path('facilities/<int:facility_pk>/polls/new/', views.poll_create, name='poll_create'),
    
    # Engagement APIs
    path('api/engagements/<int:pk>/toggle-wall/', views.toggle_engagement_wall, name='toggle_engagement_wall'),
    path('api/engagements/<int:pk>/respond/', views.respond_to_engagement, name='respond_to_engagement'),
    path('api/engagements/<int:engagement_pk>/comment/', views.add_engagement_comment, name='add_engagement_comment'),
    path('api/engagements/<int:engagement_pk>/like/', views.api_engagement_like, name='api_engagement_like'),
    path('api/polls/<int:poll_id>/vote/', views.api_poll_vote, name='api_poll_vote'),
    path('api/polls/<int:poll_id>/results/', views.api_poll_results, name='api_poll_results'),
    
    # Public anonymous comment API
    path('api/public/engagement/<int:engagement_pk>/comment/', views.add_public_comment, name='add_public_comment'),
    
    # Public wall items API (for client-side rendering)
    path('api/public/wall/<uuid:facility_uuid>/', views.api_wall_items, name='api_wall_items'),
    path('api/public/polls/<uuid:facility_uuid>/', views.api_public_polls, name='api_public_polls'),
    
    # Engagement status management (for professionals)
    path('api/engagements/<int:engagement_pk>/status/', views.api_update_engagement_status, name='api_update_engagement_status'),
    path('api/engagements/<int:engagement_pk>/delete/', views.api_delete_engagement, name='api_delete_engagement'),
    path('api/comments/<int:comment_pk>/toggle-voice/', views.api_toggle_comment_voice, name='api_toggle_comment_voice'),
    
    # Footer Pages
    path('privacy/', views.privacy_page, name='privacy'),
    path('terms/', views.terms_page, name='terms'),
    path('support/', views.support_page, name='support'),
    
    # Dashboard Search API
    path('api/dashboard-search/', views.api_dashboard_search, name='api_dashboard_search'),
]
