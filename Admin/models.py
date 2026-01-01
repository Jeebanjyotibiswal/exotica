# Admin/models.py
from django.db import models
from django.core.exceptions import ValidationError

class Result(models.Model):
    POSITION_CHOICES = [
        ('1st', '1st Place'),
        ('2nd', '2nd Place'),
        ('3rd', '3rd Place'),
    ]
    
    winner = models.CharField(max_length=50)
    branch = models.CharField(max_length=50)
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    game = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='results/')
    
    # NEW FIELD: Featured on home page
    featured = models.BooleanField(default=False, help_text="Show on home page")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def _str_(self):
        return f"{self.winner} - {self.game}"
    
    def clean(self):
        """Validate that only 3 winners can be featured"""
        if self.featured:
            # Count currently featured winners
            featured_count = Result.objects.filter(featured=True).count()
            
            # If this is a new result being featured
            if not self.pk:
                if featured_count >= 3:
                    raise ValidationError("Only 3 winners can be featured on the home page. Please unfeature another winner first.")
            else:
                # If this is an existing result being updated
                current_result = Result.objects.get(pk=self.pk)
                if not current_result.featured and featured_count >= 3:
                    raise ValidationError("Only 3 winners can be featured on the home page. Please unfeature another winner first.")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


# In models.py
from django.db import models
from django.utils import timezone

class Announcment(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    attatchment = models.FileField(upload_to='announcements/', blank=True, null=True)  # Note: attatchment (double 't')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add this line
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

# Add this to Admin/models.py
class MrMissNit(models.Model):
    YEAR_CHOICES = [
        ('2024', '2024'),
        ('2025', '2025'),
        ('2026', '2026'),
        ('2027', '2027'),
        ('2028', '2028'),
    ]
    
    year = models.CharField(max_length=4, choices=YEAR_CHOICES)
    mr_name = models.CharField(max_length=100)
    mr_photo = models.ImageField(upload_to='mr_miss_nit/')
    mr_department = models.CharField(max_length=100)
    mr_description = models.TextField(blank=True)
    
    miss_name = models.CharField(max_length=100)
    miss_photo = models.ImageField(upload_to='mr_miss_nit/')
    miss_department = models.CharField(max_length=100)
    miss_description = models.TextField(blank=True)
    
    event_description = models.TextField()
    judging_criteria = models.TextField(help_text="Enter each criterion on a new line")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Mr & Miss NIT {self.year}"
    
    def get_formatted_criteria(self):
        """
        Parse judging criteria into title and description pairs
        Format expected:
        Title Line
        Description Line
        (empty line)
        Next Title Line
        Next Description Line
        """
        criteria_list = []
        lines = self.judging_criteria.strip().split('\n')
        
        i = 0
        while i < len(lines):
            # Skip empty lines
            if not lines[i].strip():
                i += 1
                continue
            
            # Get title (current line)
            title = lines[i].strip()
            
            # Look for description (next non-empty line)
            description = ""
            i += 1
            while i < len(lines) and lines[i].strip():
                if description:
                    description += " "
                description += lines[i].strip()
                i += 1
            
            criteria_list.append({
                'title': title,
                'description': description
            })
        
        # If no criteria parsed (old format), use the simple split
        if not criteria_list:
            simple_criteria = [c.strip() for c in self.judging_criteria.split('\n') if c.strip()]
            for crit in simple_criteria:
                criteria_list.append({
                    'title': crit,
                    'description': ''
                })
        
        return criteria_list
    
    def get_criteria_list(self):
        # For backward compatibility
        return [criteria.strip() for criteria in self.judging_criteria.split('\n') if criteria.strip()]