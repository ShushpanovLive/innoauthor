from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from users.models import User
from .models import ContactMessage


def home(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'register.html')
    
def vhod(request):
    return render(request, 'vhod.html')

from users.models import User

def liderplatform(request):
    users_count = User.objects.count()
    
    return render(request, 'liderplatform.html', {
        'users_count': users_count,
    })


def workshop(request):
    return render(request, 'workshop.html')

def documents(request):
    return render(request, 'documents.html')

def shop(request):
    return render(request, 'shop.html')

def service(request):
    return render(request, 'service.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message') or request.POST.get('textarea') or ''

        if not (name and email and message_text):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
        else:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message_text,
            )
            messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
            return redirect('startpage:contact')

    return render(request, 'contact.html')
    
def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def cookie(request):
    return render(request, 'cookie.html')

def soglasie(request):
    return render(request, 'soglasie.html')

