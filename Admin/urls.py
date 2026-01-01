# Admin/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Participant management
    path('add-participant/', views.add_participant, name='add_participant'),
    path('edit-participant/<int:participant_id>/', views.edit_participant, name='edit_participant'),
    path('delete-participant/<int:participant_id>/', views.delete_participant, name='delete_participant'),
    path('export-participants/', views.export_participants, name='export_participants'),
    
    # Event management
    path('event-management/', views.event_management, name='event_management'),
    path('add-event/', views.add_event, name='add_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    
    # Add these NEW category management URLs (add them here)
    path('add-event-category/', views.add_event_category, name='add_event_category'),
    path('edit-event-category/', views.edit_event_category, name='edit_event_category'),
    path('delete-event-category/', views.delete_event_category, name='delete_event_category'),
    
    # Result management
    path('upload-result/', views.upload_result, name='upload-result'),
    path('edit-result/<int:result_id>/', views.edit_result, name='edit-result'),
    path('delete-result/<int:result_id>/', views.delete_result, name='delete-result'),
    path('toggle-featured/<int:result_id>/', views.toggle_featured, name='toggle-featured'),
    
    # Logout
    path('logout/', views.admin_logout, name='admin_logout'),
    path('announcment/', views.announcment_view, name='announcment'),

    # Add these URLs
    path('edit-announcement/<int:announcement_id>/', views.edit_announcement, name='edit_announcement'),
    path('delete-announcement/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    path('clear-all-announcements/', views.clear_all_announcements, name='clear-all-announcements'),
    
    # Mr & Miss NIT
    path('mr-miss-nit-management/', views.mr_miss_nit_management, name='mr_miss_nit_management'),
    
    # OLD - You can remove this if not using anymore
    # path('manage-event-category/', views.manage_event_category, name='manage_event_category'),
]