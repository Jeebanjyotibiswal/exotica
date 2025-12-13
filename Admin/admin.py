# Admin/admin.py - Keep this file
from django.contrib import admin
from sqlalchemy import Result
from Home.models import Event, StudentRegistration
from .models import Result,Announcment


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'category', 'get_category_display')
    list_filter = ('category',)
    search_fields = ('event_name',)
    ordering = ('category', 'event_name')
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    get_category_display.short_description = 'Category'

@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'regd_no', 'phone', 'email', 'branch', 'year', 'event', 'registered_at')
    list_filter = ('branch', 'year', 'event__category', 'registered_at')
    search_fields = ('name', 'email', 'regd_no', 'phone')
    list_per_page = 20
    date_hierarchy = 'registered_at'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone', 'regd_no')
        }),
        ('Academic Information', {
            'fields': ('branch', 'year')
        }),
        ('Event Information', {
            'fields': ('event',)
        }),
    )

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['winner', 'game', 'branch', 'position', 'featured', 'created_at']
    list_filter = ['position', 'branch', 'featured']
    search_fields = ['winner', 'game']
    list_editable = ['featured']  # Allows direct editing in list view
    actions = ['make_featured', 'remove_featured']
    
    def make_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f"Marked {queryset.count()} winners as featured")
    make_featured.short_description = "Mark selected as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(featured=False)
        self.message_user(request, f"Removed {queryset.count()} winners from featured")
    remove_featured.short_description = "Remove selected from featured"



# In admin.py
from django.contrib import admin
from .models import Announcment

@admin.register(Announcment)
class AnnouncmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']  # Now updated_at exists
    search_fields = ['title', 'content']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Optional: Make fields read-only in admin
    readonly_fields = ['created_at', 'updated_at']