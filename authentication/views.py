import os
import cv2
import numpy as np
from django.shortcuts import render
from .models import User
from django.conf import settings
import base64
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.urls import reverse

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        if not username:
            return render(request, 'register.html', {'error_message': 'Username is required'})
        
        user_image_dir = os.path.join('user_images', username)
        os.makedirs(user_image_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(0)
        image_count = 0
        while image_count < 50:
            ret, frame = cap.read()
            if not ret:
                continue
            image_path = os.path.join(user_image_dir, f'image_{image_count}.jpg')
            cv2.imwrite(image_path, frame)
            image_count += 1
        cap.release()
        
        user = User.objects.create(username=username)
        for i in range(50):
            user.images.create(image_path=os.path.join(username, f'image_{i}.jpg'))
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        faces = []
        labels = []
        for root, dirs, files in os.walk(user_image_dir):
            for file in files:
                if file.endswith(".jpg"):
                    image_path = os.path.join(root, file)
                    img = cv2.imread(image_path)
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces.append(gray)
                    labels.append(user.id)
        labels = np.array(labels)

        model_dir = os.path.join('models')
        os.makedirs(model_dir, exist_ok=True)

        recognizer.train(faces, labels)
        model_path = os.path.join(model_dir, f'{username}_model.yml')
        recognizer.save(model_path)
        
        return render(request, 'registration_success.html')
    
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        image_data = request.POST.get('image_data')

        recognizer = cv2.face.LBPHFaceRecognizer_create()

        model_path = os.path.join(settings.BASE_DIR, 'models', f'{username}_model.yml')
        if not os.path.exists(model_path):
            return render(request, 'login.html', {'error_message': 'Model not found for this user'})
        
        recognizer.read(model_path)

        image_bytes = np.frombuffer(base64.b64decode(image_data.split(',')[1]), dtype=np.uint8)
        frame = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        label, confidence = recognizer.predict(gray_frame)

        users = User.objects.filter(username=username)
        if not users.exists():
            return render(request, 'login.html', {'error_message': 'User not found'})
        user = users.first()
        if confidence < 70:
            if label == user.id:
                return render(request, 'login_success.html', {'username': user.username})
            else:
                return render(request, 'login.html', {'error_message': 'User not recognized'})
        else:
            return render(request, 'login.html', {'error_message': 'User not recognized'})
    
    return render(request, 'login.html')

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('login'))