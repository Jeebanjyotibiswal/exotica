# home/models.py
from django.db import models

# ======== ADD THIS NEW MODEL ========
class DynamicCategory(models.Model):
    """Dynamic categories that admins can add/edit/delete"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name_plural = "Dynamic Categories"
        ordering = ['name']
# ======== END OF NEW MODEL ========

# Table 1: Event List (Pre-filled) with Categories
class Event(models.Model):
    CATEGORY_CHOICES = [
        ('LITERARY', 'LITERARY EVENTS'),
        ('ATHLETICS', 'ATHLETICS EVENTS'),
        ('CULTURAL', 'CULTURAL EVENTS'),
        ('GAMES', 'GAMES'),
        ('SPORTS', 'SPORTS'),
    ]
    
    # Basic Information
    event_name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='LITERARY', null=True, blank=True)
    
    # Detailed Information for Event Page
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the event")
    rules = models.TextField(blank=True, null=True, help_text="Rules and guidelines for participants")
    judging_criteria = models.TextField(blank=True, null=True, help_text="Judging criteria for the event")
    
    # Event Logistics
    max_participants = models.IntegerField(default=1, help_text="Maximum number of participants (1 for solo, more for teams)")
    team_size = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'Solo', 'Team of 4', 'Duo', etc.")
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., '3-5 minutes', '60 minutes', 'Multiple Rounds'")
    
    # Registration Details
    registration_deadline = models.DateTimeField(blank=True, null=True, help_text="Last date for registration")
    is_active = models.BooleanField(default=True, help_text="Is this event currently open for registration?")
    
    # Admin Notes
    notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin (not visible to public)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.event_name} ({self.get_category_display()})"
    
    def get_formatted_rules(self):
        """Convert rules text into a list of points"""
        if self.rules:
            return [rule.strip() for rule in self.rules.split('\n') if rule.strip()]
        return []
    
    def get_formatted_criteria(self):
        """Convert judging criteria into a list of points"""
        if self.judging_criteria:
            return [criteria.strip() for criteria in self.judging_criteria.split('\n') if criteria.strip()]
        return []
    
    @property
    def participant_type(self):
        """Return participant type based on max_participants"""
        if self.max_participants == 1:
            return "Solo"
        elif self.max_participants == 2:
            return "Duo"
        else:
            return f"Team (max {self.max_participants})"
    
    class Meta:
        ordering = ['category', 'event_name']


class StudentRegistration(models.Model):
    YEAR_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    ]
    
    BRANCH_CHOICES = [
        ('CSE', 'CSE'),
        ('EE', 'EE'),
        ('ME', 'ME'),
        ('CIVIL', 'Civil'),
        ('MBA', 'MBA'),
        ('MCA', 'MCA'),
        ('BBA', 'BBA'),
        ('BCA', 'BCA'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    # CHANGE: college ko regd_no se replace karo
    regd_no = models.CharField(max_length=20, verbose_name="Registration Number")
    # ADD default='CSE' aur null=True
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES, default='CSE', null=True, blank=True)
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.event.event_name}"
    
    class Meta:
        ordering = ['-registered_at']