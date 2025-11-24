"""
URL configuration for exoticaa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from Home.views import home_view, about_view, contact_view, events_view, gallery_view, mr_miss_nit_view
from Home.views import registration_view
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("about/", about_view, name="about"),
    path("contact/", contact_view, name="contact"),
    path("events/", events_view, name="events"),
    path("gallery/", gallery_view, name="gallery"),
    path("mr-miss-nit/", mr_miss_nit_view, name="mr_miss_nit"),
        path("registration/", registration_view, name="registration"),
]
