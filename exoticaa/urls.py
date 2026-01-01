# exoticaa/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Home.views import (
    home_view, 
    admin_login_view, 
    about_view, 
    test_static, 
    register, 
    event_view, 
    mr_miss_nit_view,
    all_winners_view,
    notice_view,  # Add this import
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("index/", home_view, name="index"),
    path("admin-login/", admin_login_view, name="admin_login"),
    path("about/", about_view, name="about"),
    path("test/", test_static, name="test_static"),
    path("register/", register, name="register"),
    path("events/", event_view, name="events"),
    path("mr-miss-nit/", mr_miss_nit_view, name="mr-miss-nit"),
    path("winners/", all_winners_view, name="all-winners"),  # Add this line
    path("notices/", notice_view, name="notices"),  # New notices page
    
    # Include Admin app URLs
    path("admin-panel/", include('Admin.urls')),
]

# Add BOTH static and media serving
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)