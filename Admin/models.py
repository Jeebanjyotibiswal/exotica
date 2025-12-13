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