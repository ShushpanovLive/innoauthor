from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from indexglav.models import Tag
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.text import slugify
import re
from transliterate import translit
from django.contrib.contenttypes.models import ContentType
from comments.forms import CommentForm
from comments.models import Comment
from .forms import InvitationForm, TaskForm
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from django.contrib.auth import get_user_model
from django.core.paginator import PageNotAnInteger, EmptyPage
from io import BytesIO
import qrcode
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import FileResponse
from django.urls import reverse

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.paginator import PageNotAnInteger, EmptyPage
from .models import (
    Project,
    ProjectInvitation,
    Task,
    ProjectApplication,
    ProjectComplaint,
)



User = get_user_model()

def cyrillic_slugify(s):
    """Переводит строку с кириллицей в латиницу и применяет slugify"""
    if s:
        s = translit(s, 'ru', reversed=True)
        s = slugify(s)
        return s
    return ''


def projects(request):
    """Отображение списка проектов"""
    # Get all tags for filtering
    tags = Tag.objects.all()
    
    # Handle tag filtering
    current_tag = request.GET.get('tag')
    if current_tag:
        projects_list = Project.objects.filter(tags__slug=current_tag, is_private=False)
    else:
        projects_list = Project.objects.filter(is_private=False)
    
    # Handle status filtering
    current_status = request.GET.get('status')
    if current_status:
        projects_list = projects_list.filter(status=current_status)
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        projects_list = projects_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(projects_list, 10)  # Show 10 projects per page
    page = request.GET.get('page')
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    
    return render(request, 'projects.html', {
        'projects': projects,
        'tags': tags,
        'current_tag': current_tag,
        'current_status': current_status,
        'search_query': search_query,
        'status_choices': Project.STATUS_CHOICES,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator
    })


@login_required
def my_projects(request):
    # Проекты, где я автор или принятый участник
    projects_list = Project.objects.filter(
        Q(author=request.user) |
        Q(invitations__invitee=request.user, invitations__status='accepted')
    ).distinct()

    # Приглашения ко мне
    pending_invitations = ProjectInvitation.objects.filter(
        invitee=request.user,
        status='pending'
    )

    # Заявки в мои проекты
    project_applications = ProjectApplication.objects.filter(
        project__author=request.user
    )

    return render(request, 'my_projects.html', {
        'projects': projects_list,
        'pending_invitations': pending_invitations,
        'project_applications': project_applications,
    })


@login_required
def create_project(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        project_photo = request.FILES.get('project_photo')
        tag_ids = request.POST.getlist('tags')
        is_private = bool(request.POST.get('is_private'))
        
        # Проверяем уникальность имени проекта
        if Project.objects.filter(title=title).exists():
            messages.error(request, 'Проект с таким названием уже существует. Пожалуйста, выберите другое название.')
            tags = Tag.objects.all()
            return render(request, 'create_project.html', {
                'tags': tags,
                'form_data': {
                    'title': title,
                    'description': description,
                    'tag_ids': tag_ids
                }
            })
            
        # 🔥 ВСТАВЬТЕ ЗДЕСЬ (замените вашу старую проверку)
        project_photo = request.FILES.get('project_photo')
        if project_photo:
            photo_size = len(project_photo.read())
            project_photo.seek(0)
            if photo_size > 1024 * 1024:
                messages.error(request, f'Фото слишком большое: {photo_size/1024/1024:.1f} МБ')
                tags = Tag.objects.all()
                return render(request, 'create_project.html', {
                    'tags': tags,
                    'form_data': {
                        'title': title,
                        'description': description,
                        'tag_ids': tag_ids
                    }
                })
        # 🔥 КОНЕЦ ВСТАВКИ

        
        if title and description:
            project = Project.objects.create(
                title=title,
                description=description,
                author=request.user,
                project_photo=project_photo,
                slug=cyrillic_slugify(title),
                is_private=is_private
            )
            project.tags.set(tag_ids)
            print(f'project.slug: {project.slug}')
            messages.success(request, 'Проект успешно создан!')
            return redirect('projects:project_detail', project_slug=project.slug)
            
    tags = Tag.objects.all()
    return render(request, 'create_project.html', {'tags': tags})

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is author or admin
    if request.user == project.author or request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            try:
                # Manually delete related records that might cause foreign key constraint issues
                from django.db import connection
                
                with connection.cursor() as cursor:
                    # Delete any records from projects_reportproject table if it exists
                    try:
                        cursor.execute("DELETE FROM projects_reportproject WHERE project_id = %s", [project_id])
                    except Exception:
                        # Table might not exist, ignore the error
                        pass
                
                # Now delete the project (this will cascade delete related records with CASCADE)
                project.delete()
                messages.success(request, 'Проект успешно удален')
                return redirect('projects:my_projects')
            except Exception as e:
                messages.error(request, f'Ошибка при удалении проекта: {str(e)}')
                return redirect('projects:my_projects')
    else:
        messages.error(request, 'У вас нет прав для удаления этого проекта')
    
    return redirect('projects:my_projects')

def liderplatform1(request):
    # ✅ ДОБАВЬ ЭТО - подсчет пользователей
    users_count = User.objects.count()
    
    return render(request, 'glavfooter/liderplatform.html', {
        'users_count': users_count,
    })
    
def workshop1(request):
    return render(request, 'glavfooter/workshop.html')

def documents1(request):
    return render(request, 'glavfooter/documents.html')

def shop1(request):
    return render(request, 'glavfooter/shop.html')

def service1(request):
    return render(request, 'glavfooter/service.html')

def contact1(request):
    return render(request, 'glavfooter/contact.html')

# Добавляем представление для детального просмотра проекта
def project_detail(request, project_slug):
    """Отображение детальной страницы проекта"""
    project = get_object_or_404(Project, slug=project_slug)
    
    # Get comments for this project
    content_type = ContentType.objects.get_for_model(Project)
    comments = Comment.objects.filter(content_type=content_type, object_id=project.id)
    
    # Check permissions
    is_owner = request.user == project.author
    
    # Get team members
    team_members = project.team.all()
    team_members = team_members | User.objects.filter(id=project.author.id)
    is_team_member = (request.user == project.author) or (request.user in project.team.all())
    
    is_team_member = request.user in team_members
    
    # Get tasks for this project
    tasks = None
    task_form = None
    if is_team_member or is_owner:
        tasks = Task.objects.filter(project=project)
        
        # Prepare task form if user is the owner
        if is_owner:
            task_form = TaskForm(project=project)
    
    # Prepare invitation form if user is the owner
    invitation_form = None
    if is_owner:
        invitation_form = InvitationForm()
    
    # Prepare comment form
    comment_form = CommentForm()
    comment_form_action = f'/comments/projects/{project.id}/comment/'
    
    context = {
        'project': project,
        'comments': comments,
        'comment_form': comment_form,
        'comment_form_action': comment_form_action,
        'is_owner': is_owner,
        'is_team_member': is_team_member,
        'team_members': team_members,
        'invitation_form': invitation_form,
        'tasks': tasks,
        'task_form': task_form,
    }
    
    return render(request, 'project_detail.html', context)

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Проверка прав доступа
    if not (request.user == project.author or request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для редактирования этого проекта')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        project_photo = request.FILES.get('project_photo')
        tag_ids = request.POST.getlist('tags')
        
        
        # Проверка уникальности названия
        if title and title != project.title and Project.objects.filter(title=title).exists():
            messages.error(request, 'Проект с таким названием уже существует.')
            tags = Tag.objects.all()
            return render(request, 'edit_project.html', {
                'project': project,
                'tags': tags,
                'formdata': {
                    'title': title,
                    'description': description,
                    
                    'tag_ids': tag_ids
                },
                'team_members': project.team.all()  # ← НОВОЕ
            })
            
            
        # 🔥 ВСТАВЬТЕ ЗДЕСЬ (замените вашу старую проверку)
        project_photo = request.FILES.get('project_photo')
        if project_photo:
            photo_size = len(project_photo.read())
            project_photo.seek(0)
            if photo_size > 1024 * 1024:
                messages.error(request, f'Фото слишком большое: {photo_size/1024/1024:.1f} МБ')
                tags = Tag.objects.all()
                return render(request, 'create_project.html', {
                    'tags': tags,
                    'form_data': {
                        'title': title,
                        'description': description,
                        'tag_ids': tag_ids
                    }
                })
        # 🔥 КОНЕЦ ВСТАВКИ
        
        # Обновление полей
        if title:
            project.title = title
        if description:
            project.description = description
        if project_photo:
            project.project_photo = project_photo
        
        
        if title and title != project.title:
            project.slug = cyrillic_slugify(title)
        
        project.save()
        if tag_ids:
            project.tags.set(tag_ids)
        
        messages.success(request, 'Проект успешно обновлен!')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    # GET запрос - показываем форму
    tags = Tag.objects.all()
    team_members = project.team.all()  # ← НОВОЕ
    
    context = {
        'project': project,
        'tags': tags,
        'formdata': {
            'title': project.title,
            'description': project.description,
            
        },
        'team_members': team_members  # ← НОВОЕ - передаем участников в шаблон
    }
    return render(request, 'edit_project.html', context)


@login_required
def invite_member(request, project_id):
    """Send invitation to a user to join the project"""
    project = get_object_or_404(Project, id=project_id)

    # Только автор проекта может приглашать участников
    if request.user != project.author:
        messages.error(request, 'Только автор проекта может приглашать участников.')
        return redirect('projects:project_detail', project_slug=project.slug)

    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.project = project

            # Проверка по email: уже есть "висящее" приглашение
            if ProjectInvitation.objects.filter(
                project=project,
                invitee_email=invitation.invitee_email,
                status='pending'
            ).exists():
                messages.warning(
                    request,
                    f'Пользователь с email {invitation.invitee_email} уже приглашен в этот проект.'
                )
                return redirect('projects:project_detail', project_slug=project.slug)

            # Пытаемся найти пользователя по email
            try:
                user = User.objects.get(email=invitation.invitee_email)
                invitation.invitee = user

                # 1) Уже в команде или автор → приглашение НЕ создаём
                if user == project.author or user in project.team.all():
                    messages.warning(
                        request,
                        f'Пользователь {user.username} уже является участником проекта.'
                    )
                    return redirect('projects:project_detail', project_slug=project.slug)

                # 2) Уже есть заявка от этого пользователя в этот проект → не дублируем
                if ProjectApplication.objects.filter(
                    project=project,
                    applicant=user
                ).exists():
                    messages.warning(
                        request,
                        f'У пользователя {user.username} уже есть заявка в этот проект.'
                    )
                    return redirect('projects:project_detail', project_slug=project.slug)

                # 3) Уже есть другое pending‑приглашение этому пользователю
                if ProjectInvitation.objects.filter(
                    project=project,
                    invitee=user,
                    status='pending'
                ).exists():
                    messages.warning(
                        request,
                        f'Пользователю {user.username} уже отправлено приглашение.'
                    )
                    return redirect('projects:project_detail', project_slug=project.slug)

            except User.DoesNotExist:
                messages.warning(request, f'Пользователя с таким email не существует.')
                return redirect('projects:project_detail', project_slug=project.slug)

            # Если все проверки прошли — сохраняем приглашение
            invitation.save()

            invite_url = f"{request.scheme}://{request.get_host()}/projects/invitations/accept/{invitation.token}"
            email_context = {
                'project': project,
                'inviter': request.user,
                'invite_url': invite_url,
            }
            html_message = render_to_string('emails/invite.html', email_context)
            plain_message = strip_tags(html_message)

            try:
                send_mail(
                    subject=f'Приглашение в проект \"{project.title}\" на InnAuthor',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[invitation.invitee_email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception:
                messages.error(
                    request,
                    'Ошибка при отправке приглашения, возможно такого email не существует.'
                )
                return redirect('projects:project_detail', project_slug=project.slug)

            messages.success(request, f'Приглашение отправлено на {invitation.invitee_email}')
            return redirect('projects:project_detail', project_slug=project.slug)
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect('projects:project_detail', project_slug=project.slug)


@login_required
def accept_invitation(request, token):
    invitation = get_object_or_404(ProjectInvitation, token=token, status='pending')
    
    # Ensure the invitation is for the logged-in user
    if invitation.invitee and invitation.invitee != request.user:
        messages.error(request, 'Это приглашение предназначено для другого пользователя.')
        return redirect('projects:my_projects')
    
    # If invitee is not set (email invitation), set it now
    if not invitation.invitee and invitation.invitee_email == request.user.email:
        invitation.invitee = request.user
    elif not invitation.invitee and invitation.invitee_email != request.user.email:
        messages.error(request, 'Это приглашение предназначено для другого email адреса.')
        return redirect('projects:my_projects')
    
    # Accept invitation
    invitation.status = 'accepted'
    invitation.responded_at = timezone.now()
    invitation.save()
    
    messages.success(request, f'Вы успешно присоединились к проекту "{invitation.project.title}".')
    return redirect('projects:project_detail', project_slug=invitation.project.slug)

@login_required
def decline_invitation(request, token):
    invitation = get_object_or_404(ProjectInvitation, token=token, status='pending')
    
    # Ensure the invitation is for the logged-in user
    if invitation.invitee and invitation.invitee != request.user:
        messages.error(request, 'Это приглашение предназначено для другого пользователя.')
        return redirect('projects:my_projects')
    
    # If invitee is not set (email invitation), check if it matches current user's email
    if not invitation.invitee and invitation.invitee_email != request.user.email:
        messages.error(request, 'Это приглашение предназначено для другого email адреса.')
        return redirect('projects:my_projects')
    
    # Decline invitation
    invitation.status = 'declined'
    invitation.responded_at = timezone.now()
    invitation.save()
    
    messages.info(request, f'Вы отклонили приглашение в проект "{invitation.project.title}".')
    return redirect('projects:my_projects')

def verify_invitation(request):
    token = request.GET.get('token')
    if not token:
        messages.error(request, 'Неверная ссылка приглашения.')
        return redirect('indexglav:indexglav')
    
    invitation = get_object_or_404(ProjectInvitation, token=token, status='pending')
    
    # If user is not logged in, redirect to login with next parameter
    if not request.user.is_authenticated:
        messages.info(request, 'Пожалуйста, войдите в систему, чтобы принять приглашение.')
        return redirect(f'{reverse("users:login")}?next={request.path}')
    
    # If invitation has an invitee set, check if it matches current user
    if invitation.invitee and invitation.invitee != request.user:
        messages.error(request, 'Это приглашение предназначено для другого пользователя.')
        return redirect('indexglav:indexglav')
    
    # If invitation is by email, check if current user's email matches
    if not invitation.invitee and invitation.invitee_email != request.user.email:
        messages.error(request, 'Это приглашение предназначено для другого email адреса.')
        return redirect('indexglav:indexglav')
    
    return render(request, 'verify_invitation.html', {
        'invitation': invitation,
    })

@login_required
def add_task(request, project_id):
    """Add a new task to a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Only project owner can add tasks
    if request.user != project.author:
        messages.error(request, 'Только владелец проекта может добавлять задачи.')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if request.method == 'POST':
        form = TaskForm(project, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            
            messages.success(request, 'Задача успешно добавлена.')
            
            # If task was assigned to someone, notify them
            if task.assigned_to and task.assigned_to != request.user:
                # This would typically send an email notification
                pass
                
            return redirect('projects:project_detail', project_slug=project.slug)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('projects:project_detail', project_slug=project.slug)

@login_required
def update_task(request, task_id):
    """Update an existing task"""
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    
    # Only project owner or task assignee can update
    if request.user != project.author and request.user != task.assigned_to:
        messages.error(request, 'У вас нет прав для изменения этой задачи.')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if request.method == 'POST':
        # Project owner can edit all fields, assignee can only update status
        if request.user == project.author:
            form = TaskForm(project, request.POST, instance=task)
        else:
            form = TaskForm(project, request.POST, instance=task)
            form.fields.pop('title')
            form.fields.pop('description')
            form.fields.pop('assigned_to')
            form.fields.pop('deadline')
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена.')
            return redirect('projects:project_detail', project_slug=project.slug)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('projects:project_detail', project_slug=project.slug)

@login_required
def delete_task(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    
    # Only project owner can delete tasks
    if request.user != project.author:
        messages.error(request, 'Только владелец проекта может удалять задачи.')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача успешно удалена.')
    
    return redirect('projects:project_detail', project_slug=project.slug)
    
    

@login_required
def project_application(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user == project.author or request.user in project.team.all():
        messages.warning(request, 'Вы уже участник этого проекта')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if ProjectApplication.objects.filter(project=project, applicant=request.user).exists():
        messages.warning(request, 'Заявка уже подана')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        ProjectApplication.objects.create(
            project=project, 
            applicant=request.user, 
            message=message
        )
        messages.success(request, 'Заявка отправлена владельцу проекта!')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    return render(request, 'project_application.html', {'project': project})

@login_required
def project_complaint(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        ProjectComplaint.objects.create(
            project=project, 
            complainant=request.user, 
            reason=reason
        )
        messages.success(request, 'Жалоба отправлена администратору!')
        return redirect('projects:project_detail', project_slug=project.slug)
    return render(request, 'project_complaint.html', {'project': project})






@login_required
def accept_application(request, application_id):
    application = get_object_or_404(ProjectApplication, id=application_id)
    if request.user != application.project.author:
        messages.error(request, 'Нет прав')
        return redirect('projects:my_projects')
    
    project = application.project
    applicant = application.applicant

    # Если уже есть accepted‑приглашение — просто чистим заявку
    invitation, created = ProjectInvitation.objects.get_or_create(
        project=project,
        invitee=applicant,
        defaults={'status': 'accepted'}
    )
    if not created and invitation.status != 'accepted':
        invitation.status = 'accepted'
        invitation.save()

    # Чистим лишние pending‑приглашения (если дубли были)
    ProjectInvitation.objects.filter(
        project=project,
        invitee=applicant
    ).exclude(id=invitation.id).delete()

    # Удаляем заявку
    application.delete()

    messages.success(request, f'{applicant.username} принят в проект!')
    return redirect('projects:project_detail', project_slug=project.slug)



@login_required
def reject_application(request, application_id):
    application = get_object_or_404(ProjectApplication, id=application_id)
    if request.user != application.project.author:
        messages.error(request, 'Нет прав')
        return redirect('projects:my_projects')
    
    application.delete()
    messages.info(request, 'Заявка отклонена')
    return redirect('projects:my_projects')


def public_profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    context = {
        'profile_user': user_obj,
    }
    return render(request, 'users/profile.html', context)
    
    


@login_required
def removeteammember(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    user_to_remove = get_object_or_404(User, id=user_id)
    
    # ✅ НОВЫЕ ПРАВИЛА
    if request.user != project.author and user_to_remove != request.user:
        messages.error(request, 'У вас нет прав для удаления участников.')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    if request.method == 'POST':
        project.team.remove(user_to_remove)
        if user_to_remove == request.user:
            messages.success(request, 'Вы успешно вышли из проекта.')
        else:
            messages.success(request, f'Участник {user_to_remove.username} удалён из команды.')
        return redirect('projects:project_detail', project_slug=project.slug)
    
    return redirect('projects:project_detail', project_slug=project.slug)

def split_long_word(pdf, word, font_name, font_size, max_width):
    """
    Делит длинное слово по символам.
    Нужна на случай, когда пользователь ввёл 50 символов подряд без пробелов.
    """
    parts = []
    current_part = ""

    for char in word:
        candidate = current_part + char

        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current_part = candidate
        else:
            if current_part:
                parts.append(current_part)

            current_part = char

    if current_part:
        parts.append(current_part)

    return parts


def wrap_pdf_text(pdf, text, font_name, font_size, max_width):
    """
    Переносит текст по словам.

    Если одно слово длиннее допустимой ширины,
    оно дополнительно разделяется по символам.
    """
    text = str(text or "").strip()
    words = text.split()

    if not words:
        return [""]

    lines = []
    current_line = ""

    for word in words:
        word_width = pdf.stringWidth(word, font_name, font_size)

        # Слово не помещается даже само по себе.
        if word_width > max_width:
            # Сохраняем строку, которую уже собрали.
            if current_line:
                lines.append(current_line)
                current_line = ""

            # Делим большое слово на подходящие части.
            word_parts = split_long_word(
                pdf=pdf,
                word=word,
                font_name=font_name,
                font_size=font_size,
                max_width=max_width
            )

            # Все части, кроме последней, уже являются готовыми строками.
            lines.extend(word_parts[:-1])

            # Последняя часть может поместиться вместе со следующим словом.
            current_line = word_parts[-1]
            continue

        candidate = f"{current_line} {word}".strip()

        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
        else:
            if current_line:
                lines.append(current_line)

            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def draw_wrapped_centered_text(
    pdf,
    text,
    y,
    font_name,
    font_size,
    color,
    max_width,
    line_spacing
):
    """
    Печатает текст по центру с переносом строк.
    Возвращает координату Y после последней строки.
    """
    pdf.setFillColor(color)
    pdf.setFont(font_name, font_size)

    lines = wrap_pdf_text(
        pdf=pdf,
        text=text,
        font_name=font_name,
        font_size=font_size,
        max_width=max_width
    )

    for line in lines:
        pdf.drawCentredString(
            A4[0] / 2,
            y,
            line
        )
        y -= line_spacing

    return y


@login_required
def project_certificate(request, project_slug):
    """
    Формирует PDF-сертификат проекта.

    Сертификат может скачать:
    - автор проекта;
    - сотрудник сайта;
    - суперпользователь.
    """

    project = get_object_or_404(Project, slug=project_slug)

    # Проверка доступа.
    if not (
        request.user == project.author
        or request.user.is_staff
        or request.user.is_superuser
    ):
        messages.error(
            request,
            "У вас нет прав для получения сертификата этого проекта."
        )
        return redirect(
            "projects:project_detail",
            project_slug=project.slug
        )

    # URL публичной страницы проекта — его записываем в QR-код.
    project_path = reverse(
        "projects:project_detail",
        kwargs={"project_slug": project.slug}
    )
    project_url = request.build_absolute_uri(project_path)

    # QR-код в памяти.
    qr_buffer = BytesIO()

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2
    )
    qr.add_data(project_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    qr_image.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # PDF в памяти.
    pdf_buffer = BytesIO()

    # Подключение шрифтов с кириллицей.
    fonts_dir = settings.BASE_DIR / "projects" / "fonts"

    regular_font_path = fonts_dir / "DejaVuSans.ttf"
    bold_font_path = fonts_dir / "DejaVuSans-Bold.ttf"

    if not regular_font_path.exists() or not bold_font_path.exists():
        raise FileNotFoundError(
            "Не найдены шрифты для PDF. "
            "Добавьте в папку projects/fonts файлы "
            "DejaVuSans.ttf и DejaVuSans-Bold.ttf."
        )

    # Регистрируем шрифты, только если они ещё не зарегистрированы.
    if "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("DejaVuSans", str(regular_font_path))
        )

    if "DejaVuSans-Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("DejaVuSans-Bold", str(bold_font_path))
        )

    # Создаём A4 PDF.
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

    page_width, page_height = A4

    # Фирменная палитра ИнноАвтор.
    background_color = HexColor("#11213B")
    text_color = HexColor("#FFFFFF")
    accent_color = HexColor("#EE8634")

    # Фон страницы.
    pdf.setFillColor(background_color)
    pdf.rect(
        0,
        0,
        page_width,
        page_height,
        fill=1,
        stroke=0
    )

    # Основная декоративная рамка.
    border_margin = 1.1 * cm

    pdf.setStrokeColor(accent_color)
    pdf.setLineWidth(1.5)

    pdf.roundRect(
        border_margin,
        border_margin,
        page_width - 2 * border_margin,
        page_height - 2 * border_margin,
        12,
        fill=0,
        stroke=1
    )

    # Верхняя декоративная оранжевая линия.
    pdf.setFillColor(accent_color)

    pdf.roundRect(
        (page_width / 2) - 3.0 * cm,
        page_height - 2.1 * cm,
        6.0 * cm,
        0.22 * cm,
        3,
        fill=1,
        stroke=0
    )

    # Данные проекта.
    project_title = project.title or "Без названия"

    author_name = project.author.get_full_name().strip()
    if not author_name:
        author_name = project.author.username

    created_datetime = timezone.localtime(project.create_datetime)
    created_text = created_datetime.strftime("%d.%m.%Y в %H:%M")

    tags = list(project.tags.values_list("name", flat=True))
    tags_text = " · ".join(tags[:5]) if tags else "Без меток"

    # Заголовок «Сертификат».
    pdf.setFillColor(text_color)
    pdf.setFont("DejaVuSans-Bold", 27)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 4.2 * cm,
        "СЕРТИФИКАТ"
    )

    # Название проекта.
    title_font_name = "DejaVuSans-Bold"
    title_font_size = 18
    title_max_width = page_width - 5.2 * cm

    project_title_lines = wrap_pdf_text(
        pdf=pdf,
        text=project_title,
        font_name=title_font_name,
        font_size=title_font_size,
        max_width=title_max_width
    )

    # Если название превратилось в 3+ строки,
    # уменьшаем шрифт, чтобы оно смотрелось аккуратно.
    if len(project_title_lines) > 2:
        title_font_size = 15

        project_title_lines = wrap_pdf_text(
            pdf=pdf,
            text=project_title,
            font_name=title_font_name,
            font_size=title_font_size,
            max_width=title_max_width
        )

    # Даже при строке из 50 одинаковых символов
    # название никогда не выйдет за левую и правую рамки.
    pdf.setFillColor(accent_color)
    pdf.setFont(title_font_name, title_font_size)

    title_y = page_height - 6.0 * cm
    title_line_spacing = 0.82 * cm

    for line in project_title_lines:
        pdf.drawCentredString(
            page_width / 2,
            title_y,
            line
        )
        title_y -= title_line_spacing

    # Основной текст автоматически идёт ниже названия.
    info_y = title_y - 0.55 * cm
    info_max_width = page_width - 5.0 * cm

    info_y = draw_wrapped_centered_text(
        pdf=pdf,
        text="Настоящим подтверждается создание проекта указанным автором в указанную дату и время.",
        y=info_y,
        font_name="DejaVuSans",
        font_size=12,
        color=text_color,
        max_width=info_max_width,
        line_spacing=0.62 * cm
    )

    info_y -= 0.18 * cm

    info_y = draw_wrapped_centered_text(
        pdf=pdf,
        text=f"Дата и время создания: {created_text}",
        y=info_y,
        font_name="DejaVuSans",
        font_size=11,
        color=text_color,
        max_width=info_max_width,
        line_spacing=0.58 * cm
    )

    info_y -= 0.14 * cm

    info_y = draw_wrapped_centered_text(
        pdf=pdf,
        text=f"Автор проекта: {author_name}",
        y=info_y,
        font_name="DejaVuSans",
        font_size=11,
        color=text_color,
        max_width=info_max_width,
        line_spacing=0.58 * cm
    )

    info_y -= 0.45 * cm

    info_y = draw_wrapped_centered_text(
        pdf=pdf,
        text="Проект опубликован на цифровой платформе «ИнноАвтор»",
        y=info_y,
        font_name="DejaVuSans",
        font_size=10,
        color=text_color,
        max_width=info_max_width,
        line_spacing=0.52 * cm
    )

    info_y -= 0.12 * cm

    draw_wrapped_centered_text(
        pdf=pdf,
        text=f"Метки: {tags_text}",
        y=info_y,
        font_name="DejaVuSans",
        font_size=9,
        color=text_color,
        max_width=info_max_width,
        line_spacing=0.48 * cm
    )

    # QR-код со ссылкой на страницу проекта.
    qr_size = 4.1 * cm
    qr_x = (page_width - qr_size) / 2
    qr_y = 5.0 * cm

    # Белая подложка нужна для корректного сканирования QR-кода.
    pdf.setFillColor(text_color)

    pdf.roundRect(
        qr_x - 0.18 * cm,
        qr_y - 0.18 * cm,
        qr_size + 0.36 * cm,
        qr_size + 0.36 * cm,
        6,
        fill=1,
        stroke=0
    )

    pdf.drawImage(
        ImageReader(qr_buffer),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        mask="auto"
    )

    # Подпись под QR-кодом.
    pdf.setFillColor(text_color)
    pdf.setFont("DejaVuSans", 9)

    pdf.drawCentredString(
        page_width / 2,
        4.25 * cm,
        "Отсканируйте QR-код, чтобы открыть страницу проекта"
    )

    # Линия перед подписью.
    pdf.setStrokeColor(accent_color)
    pdf.setLineWidth(0.8)

    pdf.line(
        3.0 * cm,
        3.35 * cm,
        page_width - 3.0 * cm,
        3.35 * cm
    )

    # Подпись создателя платформы.
    pdf.setFillColor(text_color)
    pdf.setFont("DejaVuSans", 10)

    pdf.drawCentredString(
        page_width / 2,
        2.65 * cm,
        "Создатель платформы «ИнноАвтор»"
    )

    pdf.setFillColor(accent_color)
    pdf.setFont("DejaVuSans-Bold", 13)

    pdf.drawCentredString(
        page_width / 2,
        2.05 * cm,
        "Михаил Шушпанов"
    )

    # Завершаем PDF.
    pdf.save()
    pdf_buffer.seek(0)

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=f"certificate-innoavtor-{project.id}.pdf",
        content_type="application/pdf"
    )

from django.shortcuts import render

def step1(request):
    return render(request, 'step1.html')

def step2(request):
    return render(request, 'step2.html')
    
def step3(request):
    return render(request, 'step3.html')

def step4(request):
    return render(request, 'step4.html')
    
def step5(request):
    return render(request, 'step5.html')
