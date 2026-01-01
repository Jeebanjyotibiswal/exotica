# Admin/admin.py
from django.contrib import admin
from Home.models import Event, StudentRegistration
from .models import Result, Announcment, MrMissNit

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'category', 'max_participants', 'team_size', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('event_name', 'description')
    list_editable = ('is_active', 'max_participants')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event_name', 'category', 'is_active')
        }),
        ('Event Details', {
            'fields': ('description', 'rules', 'judging_criteria')
        }),
        ('Event Logistics', {
            'fields': ('max_participants', 'team_size', 'duration', 'registration_deadline')
        }),
        ('Internal Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)  # Makes this section collapsible
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make created_at and updated_at read-only
        if obj:
            return self.readonly_fields + ('created_at', 'updated_at')
        return self.readonly_fields

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

@admin.register(Announcment)
class AnnouncmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
    search_fields = ['title', 'content']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Optional: Make fields read-only in admin
    readonly_fields = ['created_at', 'updated_at']

@admin.register(MrMissNit)
class MrMissNitAdmin(admin.ModelAdmin):
    list_display = ('year', 'mr_name', 'miss_name', 'created_at')
    list_filter = ('year',)
    search_fields = ('mr_name', 'miss_name', 'mr_department', 'miss_department')
    fieldsets = (
        ('Year Information', {
            'fields': ('year',)
        }),
        ('Mr. NIT Details', {
            'fields': ('mr_name', 'mr_photo', 'mr_department', 'mr_description')
        }),
        ('Miss NIT Details', {
            'fields': ('miss_name', 'miss_photo', 'miss_department', 'miss_description')
        }),
        ('Event Content', {
            'fields': ('event_description', 'judging_criteria'),
            'description': 'Enter the event description and judging criteria (one per line)'
        }),
    )