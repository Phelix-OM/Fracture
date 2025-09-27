from django.db import models
import os
from django.utils import timezone

class FractureDetection(models.Model):
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    prediction = models.CharField(max_length=100, blank=True)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Detection {self.id} - {self.prediction}"
    
    def delete(self, *args, **kwargs):
        # Delete the image file when the model is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)