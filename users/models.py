from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from uuid import uuid4

class User(AbstractUser):
    """Custom User model that extends AbstractUser."""
    
    email = models.EmailField(_('email address'), unique=True)
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр разрешено."
    )
    phone = models.CharField('Телефон', validators=[phone_regex], max_length=17, blank=True)
    
    email_verified = models.BooleanField('Email подтвержден', default=False)
    phone_verified = models.BooleanField('Телефон подтвержден', default=False)
    
    verification_token = models.CharField(max_length=100, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)
    patronymic = models.CharField('Отчество', max_length=150, blank=True, null=True)
    ip_address = models.GenericIPAddressField('IP адрес регистрации', null=True, blank=True)
    
    about = models.TextField('О себе', blank=True, null=True)
    avatar = models.ImageField('Фото профиля', upload_to='static/img/avatars', blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def generate_verification_token(self):
        """Generate a verification token with timestamp."""
        self.verification_token = str(uuid4())
        self.token_created_at = timezone.now()
        self.save(update_fields=['verification_token', 'token_created_at'])
        return self.verification_token
    
    def verify_email(self):
        """Mark email as verified."""
        self.email_verified = True
        self.verification_token = ''
        self.token_created_at = None
        self.save(update_fields=['email_verified', 'verification_token', 'token_created_at'])
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


