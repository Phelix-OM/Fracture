from django import forms
from .models import FractureDetection
import os

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = FractureDetection
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            })
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (10MB limit)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 10MB )")
            
            # Check file extension
            ext = os.path.splitext(image.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            if ext not in valid_extensions:
                raise forms.ValidationError("Unsupported file extension.")
        
        return image