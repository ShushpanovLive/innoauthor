from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .forms import RegisterUserForm

def get_client_ip(request):
    """Получает IP-адрес клиента из запроса."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def accounts(request):
    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Сохраняем IP-адрес пользователя
            user.ip_address = get_client_ip(request)
            user.save()
            
            # После сохранения пользователя, выполняем необходимые действия из формы
            form.save_m2m()  # Сохраняем связи Many-to-Many если они есть
            
            # Генерируем токен верификации
            user.generate_verification_token()
            
            # Generate verification URL
            verification_url = f"{request.scheme}://{request.get_host()}/users/verify/{user.verification_token}/"
            
            # Prepare email context
            email_context = {
                'user': user,
                'verification_url': verification_url,
            }
            
            # Render email templates
            html_message = render_to_string('emails/verify_email.html', email_context)
            plain_message = strip_tags(html_message)
            
            # Send verification email
            send_mail(
                subject='Подтверждение регистрации на InnoAuthor',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            messages.success(request, 'Регистрация успешна! Пожалуйста, проверьте вашу почту для подтверждения аккаунта.')
            return redirect('users:login')
        else:
            messages.error(request, 'Ошибка регистрации. Пожалуйста, проверьте данные.')
    else:
        form = RegisterUserForm()
    return render(request, 'accounts/register.html', {'form': form})

