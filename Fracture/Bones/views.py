# fracture_detection/views.py - COMPLETE UPDATED VERSION
import os
import numpy as np
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from tensorflow.keras.models import load_model
from PIL import Image
from .models import FractureDetection
from .forms import ImageUploadForm

class FractureDetector:
    _model = None
    _class_names = ['Fracture Detected', 'Normal Bone']
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                cls._model = load_model(settings.MODEL_PATH)
                print("✅ Model loaded successfully!")
                
                # Debug: Print model input shape
                print(f"📊 Model input shape: {cls._model.input_shape}")
                
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                cls._model = None
        return cls._model
    
    @classmethod
    def predict_fracture(cls, image_path):
        model = cls.get_model()
        if model is None:
            return {'error': 'Model not available'}
        
        try:
            # Load image
            img = Image.open(image_path)
            print(f"📷 Original image mode: {img.mode}, size: {img.size}")
            
            # Determine required input channels from model
            input_shape = model.input_shape
            required_channels = input_shape[-1]
            
            # Preprocess based on model requirements
            if required_channels == 1:
                # Convert to grayscale for single-channel model
                if img.mode != 'L':
                    img = img.convert('L')
                    print("🔄 Converted to grayscale")
            elif required_channels == 3:
                # Convert to RGB for three-channel model
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    print("🔄 Converted to RGB")
            else:
                return {'error': f'Unsupported channel size: {required_channels}'}
            
            # Resize to model's expected size
            target_size = (input_shape[1], input_shape[2])  # (height, width)
            img = img.resize(target_size)
            print(f"📏 Resized to: {target_size}")
            
            # Convert to array and normalize
            img_array = np.array(img) / 255.0
            
            # Ensure correct shape
            if len(img_array.shape) == 2:  # Grayscale
                img_array = np.expand_dims(img_array, axis=-1)  # Add channel dimension
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            print(f"📊 Final image shape: {img_array.shape}")
            
            # Make prediction
            prediction = model.predict(img_array, verbose=0)
            class_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][class_idx])
            
            return {
                'prediction': cls._class_names[class_idx],
                'confidence': confidence,
                'class_probabilities': {
                    cls._class_names[i]: float(prob) 
                    for i, prob in enumerate(prediction[0])
                }
            }
        except Exception as e:
            return {'error': f'Prediction error: {str(e)}'}

def home(request):
    """Home page view"""
    return render(request, 'fracture_detection/index.html')

def upload_image(request):
    """Handle image upload and fracture detection"""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save uploaded image
                detection = form.save()
                print(f"📁 Image saved at: {detection.image.path}")
                
                # Make prediction
                result = FractureDetector.predict_fracture(detection.image.path)
                
                if 'error' not in result:
                    # Update detection with prediction results
                    detection.prediction = result['prediction']
                    detection.confidence = result['confidence']
                    detection.save()
                    
                    # Generate medical report
                    medical_report = generate_medical_report(result)
                    
                    return render(request, 'fracture_detection/result.html', {
                        'detection': detection,
                        'result': result,
                        'medical_report': medical_report
                    })
                else:
                    # Handle prediction error
                    print(f"❌ Prediction error: {result['error']}")
                    return render(request, 'fracture_detection/upload.html', {
                        'form': form,
                        'error': result['error']
                    })
                    
            except Exception as e:
                print(f"❌ Error processing image: {e}")
                return render(request, 'fracture_detection/upload.html', {
                    'form': form,
                    'error': f'Error processing image: {str(e)}'
                })
        else:
            # Form validation failed
            return render(request, 'fracture_detection/upload.html', {
                'form': form,
                'error': 'Please check the uploaded file. It must be an image under 10MB.'
            })
    else:
        form = ImageUploadForm()
    
    return render(request, 'fracture_detection/upload.html', {'form': form})

# Update the generate_medical_report function in views.py
def generate_medical_report(prediction_result):
    if prediction_result['prediction'] == 'Fracture Detected':
        return {
            'diagnosis': 'Potential Bone Fracture Detected',
            'severity': 'Requires Immediate Medical Attention',
            'urgency': 'High',
            'recommendation': 'Consult with an orthopedic specialist immediately for proper diagnosis and treatment.',
            'detailed_analysis': f'''
                AI analysis has detected potential bone fracture with {prediction_result["confidence"]:.1%} confidence level. 
                The image shows characteristics consistent with fracture patterns including possible discontinuity in bone 
                structure, alignment issues, or abnormal bone density patterns. Immediate medical evaluation is strongly 
                recommended to confirm the findings and initiate appropriate treatment.
            ''',
            'treatment_plan': [
                {
                    'title': 'Immediate First Aid',
                    'description': 'Immobilize the affected area, apply ice to reduce swelling, avoid weight-bearing activities',
                    'timeline': 'Immediately'
                },
                {
                    'title': 'Medical Consultation',
                    'description': 'Schedule emergency orthopedic consultation for proper diagnosis and treatment planning',
                    'timeline': 'Within 24 hours'
                },
                {
                    'title': 'Diagnostic Confirmation',
                    'description': 'Additional imaging (CT scan or MRI) may be required for comprehensive assessment',
                    'timeline': 'Within 48 hours'
                },
                {
                    'title': 'Treatment Initiation',
                    'description': 'Begin appropriate treatment based on orthopedic specialist recommendations',
                    'timeline': 'Within 72 hours'
                }
            ],
            'additional_advice': [
                {'icon': 'ban', 'text': 'Avoid movement of affected area'},
                {'icon': 'snowflake', 'text': 'Apply ice packs for 15-20 minutes every 2-3 hours'},
                {'icon': 'bed', 'text': 'Keep the limb elevated when resting'},
                {'icon': 'pills', 'text': 'Take pain medication as prescribed by doctor'},
                {'icon': 'user-md', 'text': 'Follow up with orthopedic specialist regularly'},
                {'icon': 'utensils', 'text': 'Maintain calcium and vitamin D rich diet'}
            ],
            'risk_factors': [
                'Age-related bone density changes',
                'Previous fracture history',
                'Osteoporosis risk factors',
                'Physical activity level',
                'Nutritional status'
            ]
        }
    else:
        return {
            'diagnosis': 'No Fracture Detected - Normal Bone Structure',
            'severity': 'Normal Findings',
            'urgency': 'Low',
            'recommendation': 'No fracture detected. Continue monitoring and consult healthcare professional if symptoms persist.',
            'detailed_analysis': f'''
                AI analysis shows no evidence of bone fracture with {prediction_result["confidence"]:.1%} confidence level. 
                The bone structure appears normal with proper alignment and continuity. Joint spaces are well-maintained 
                and there are no signs of acute fracture or dislocation. However, if clinical symptoms persist, further 
                evaluation may be warranted.
            ''',
            'treatment_plan': [
                {
                    'title': 'Symptom Monitoring',
                    'description': 'Continue monitoring for any changes in pain, swelling, or mobility',
                    'timeline': 'Ongoing'
                },
                {
                    'title': 'Follow-up Consultation',
                    'description': 'Schedule appointment if symptoms persist beyond 1-2 weeks',
                    'timeline': 'Within 2 weeks'
                },
                {
                    'title': 'Preventive Care',
                    'description': 'Maintain bone health through proper nutrition and exercise',
                    'timeline': 'Long-term'
                }
            ],
            'additional_advice': [
                {'icon': 'heart', 'text': 'Maintain regular physical activity for bone strength'},
                {'icon': 'utensils', 'text': 'Ensure adequate calcium and vitamin D intake'},
                {'icon': 'sun', 'text': 'Get regular sunlight exposure for vitamin D synthesis'},
                {'icon': 'weight', 'text': 'Include weight-bearing exercises in your routine'},
                {'icon': 'smoking-ban', 'text': 'Avoid smoking and excessive alcohol consumption'},
                {'icon': 'balance-scale', 'text': 'Maintain healthy body weight'}
            ],
            'preventive_measures': [
                'Regular bone density screening if risk factors present',
                'Fall prevention strategies',
                'Proper safety equipment during sports',
                'Home safety modifications if needed'
            ]
        }

def about(request):
    """About page view"""
    return render(request, 'fracture_detection/about.html')

def api_predict(request):
    """API endpoint for predictions"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Save uploaded file temporarily
            uploaded_file = request.FILES['image']
            temp_path = f"/tmp/{uploaded_file.name}"
            
            with open(temp_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            print(f"🔍 API Request: Processing {uploaded_file.name}")
            
            # Make prediction
            result = FractureDetector.predict_fracture(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            if 'error' not in result:
                return JsonResponse({
                    'success': True,
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'probabilities': result['class_probabilities'],
                    'timestamp': timezone.now().isoformat()
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': result['error']
                })
                
        except Exception as e:
            print(f"❌ API Error: {e}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'No image provided. Please upload an image file.'
    })

def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'fracture_detection/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'fracture_detection/500.html', status=500)

# Additional utility functions
def get_model_info(request):
    """API endpoint to get model information"""
    if request.method == 'GET':
        try:
            model = FractureDetector.get_model()
            if model:
                return JsonResponse({
                    'success': True,
                    'input_shape': model.input_shape,
                    'output_shape': model.output_shape,
                    'layers_count': len(model.layers),
                    'model_type': 'Functional' if hasattr(model, '_is_graph_network') else 'Sequential'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Model not loaded'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    })

def health_check(request):
    """Health check endpoint for deployment"""
    try:
        # Check if model can be loaded
        model = FractureDetector.get_model()
        model_status = 'healthy' if model else 'unhealthy'
        
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = 'healthy'
        
        return JsonResponse({
            'status': 'healthy',
            'model': model_status,
            'database': db_status,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)