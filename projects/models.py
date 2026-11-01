from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from indexglav.models import Tag
from uuid import uuid4
from django.core.validators import FileExtensionValidator
User = get_user_model()





class ProjectInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('accepted', 'Принято'),
        ('declined', 'Отклонено'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='invitations')
    invitee_email = models.EmailField(verbose_name='Email приглашаемого')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='invitations')
    token = models.CharField(max_length=100, unique=True, default=uuid4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Приглашение в проект'
        verbose_name_plural = 'Приглашения в проекты'
        
    def __str__(self):
        return f'Приглашение в {self.project.title} для {self.invitee_email}'

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает выполнения'),
        ('in_progress', 'В процессе'),
        ('completed', 'Выполнено'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name='Название задачи')
    description = models.TextField(blank=True, verbose_name='Описание задачи')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks', verbose_name='Создатель')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name='Исполнитель')
    deadline = models.DateField(null=True, blank=True, verbose_name='Срок выполнения')
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['status', 'deadline', '-created_at']
    
    def __str__(self):
        return self.title

class Project(models.Model):
    STATUS_CHOICES = [
        ('concept', 'Идея'),
        ('launch', 'Рабочая модель'),
        ('ready_project', 'Готовый проект'),
        ('business', 'Бизнес'),  # ← НОВОЕ
	('prospective', 'Перспективный'),
    ]
    
    title = models.CharField('Название проекта', max_length=200)
    description = models.TextField('Описание проекта')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', related_name='authored_projects')
    create_datetime = models.DateTimeField('Дата создания', auto_now_add=True)
    project_photo = models.ImageField('Фото проекта', upload_to='projects/', blank=True)
    slug = models.SlugField('URL', unique=True)
    tags = models.ManyToManyField(Tag, verbose_name='Теги', related_name='projects')
    team = models.ManyToManyField(User, through=ProjectInvitation, verbose_name='Команда', related_name='projects')
    status = models.CharField('Статус проекта', max_length=20, choices=STATUS_CHOICES, default='concept')
    is_private = models.BooleanField('Приватный', default=False)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-create_datetime']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title




class ProjectApplication(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_applications')
    message = models.TextField(blank=True, verbose_name='Сопроводительное сообщение')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Заявка в проект'
        verbose_name_plural = 'Заявки в проекты'
    
    def __str__(self):
        return f'Заявка от {self.applicant.username} в "{self.project.title}"'

class ProjectComplaint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='complaints')
    complainant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_complaints')
    reason = models.TextField(verbose_name='Причина жалобы')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Жалоба на проект'
        verbose_name_plural = 'Жалобы на проекты'
    
    def __str__(self):
        return f'Жалоба на "{self.project.title}" от {self.complainant.username}'
