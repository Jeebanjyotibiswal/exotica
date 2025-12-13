# home/models.py
from django.db import models

# Table 1: Event List (Pre-filled) with Categories
class Event(models.Model):
    CATEGORY_CHOICES = [
        ('LITERARY', 'LITERARY EVENTS'),
        ('ATHLETICS', 'ATHLETICS EVENTS'),
        ('CULTURAL', 'CULTURAL EVENTS'),
        ('GAMES', 'GAMES'),
        ('SPORTS', 'SPORTS'),
    ]
    
    event_name = models.CharField(max_length=200)
    # ADD default='LITERARY' aur null=True
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='LITERARY', null=True, blank=True)
    
    def _str_(self):
        return f"{self.event_name} ({self.get_category_display()})"
    
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
    
    def _str_(self):
        return f"{self.name} - {self.event.event_name}"
    
    class Meta:
        ordering = ['-registered_at']