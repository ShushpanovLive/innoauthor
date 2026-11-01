"""
URL configuration for InnAuthor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from indexglav.views import liderplatform
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views

from . import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('liderplatform/', liderplatform, name='liderplatform'),
    path('users/', include('users.urls', namespace="users")),
    path('', include('startpage.urls', namespace="startpage")),
    path('news/', include('indexglav.urls', namespace="indexglav")),
    path('projects/', include('projects.urls', namespace="projects")),
    path('about/', include('about.urls', namespace="about")),
    path('exite/', include('exite.urls', namespace="exite")),
    path('accounts/', include('accounts.urls', namespace="accounts")),
    path('comments/', include('comments.urls', namespace="comments")),

    # Password reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
        name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
        name='password_reset_complete'),
]

# Добавляем поддержку статических файлов в режиме отладки
urlpatterns += staticfiles_urlpatterns()

# Добавляем обработку медиа файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
