# fracture_detection/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_image, name='upload_image'),
    path('about/', views.about, name='about'),
    path('api/predict/', views.api_predict, name='api_predict'),
    path('api/model-info/', views.get_model_info, name='model_info'),
    path('health/', views.health_check, name='health_check'),
]

# Error handlers
handler404 = views.handler404
handler500 = views.handler500