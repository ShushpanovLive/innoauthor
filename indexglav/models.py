from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.text import slugify

User = get_user_model()

class Tag(models.Model):
    name = models.CharField('Название тега', max_length=50, unique=True)
    slug = models.SlugField('URL', unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name

class Newspost(models.Model):
    namepost = models.CharField('Название поста', max_length=100)
    humanpost = models.CharField('От кого новость', max_length=100)
    soderjanie = models.TextField('Содержание поста')
    postdate = models.DateTimeField('Дата и время поста', auto_now_add=True)
    post_photo = models.ImageField('Фото', upload_to='static/img', blank=True)
    slug = models.SlugField('URL', unique=True, blank=True)
    tags = models.ManyToManyField(Tag, verbose_name='Теги', related_name='news_posts')

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-postdate']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.namepost)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.namepost

class Expert(models.Model):
    name = models.CharField('ФИО', max_length=100)
    photo = models.ImageField('Фото', upload_to='experts/', blank=True)
    text = models.TextField('Описание', max_length=200)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Эксперта'
        verbose_name_plural = 'Эксперты'
