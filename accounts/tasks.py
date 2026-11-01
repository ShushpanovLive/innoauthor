from celery_app import app
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

@app.task
def send_verification_email(user_id, verification_url):
    """Отправить email верификации асинхронно через Celery"""
    from users.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        email_context = {
            'user': user,
            'verification_url': verification_url,
        }
        
        html_message = render_to_string('emails/verify_email.html', email_context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Подтверждение регистрации на InnoAuthor',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return f"Email sent to {user.email}"
    except Exception as e:
        return f"Error: {str(e)}"
