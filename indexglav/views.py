from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from .models import Newspost, Tag
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from comments.forms import CommentForm
from comments.models import Comment
from .models import Expert

def indexglav(request):
    tag_slug = request.GET.get('tag')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    vivodnews = Newspost.objects.all()
    
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        vivodnews = vivodnews.filter(tags=tag)
        
    if search_query:
        vivodnews = vivodnews.filter(
            Q(namepost__icontains=search_query) |
            Q(soderjanie__icontains=search_query) |
            Q(humanpost__icontains=search_query)
        )
    
    # Пагинация: показываем максимум 10 новостей на странице
    paginator = Paginator(vivodnews, 10)
    page_obj = paginator.get_page(page)
    
    tags = Tag.objects.all()
    return render(request, 'indexglav.html', {
        'vivodnews': page_obj,
        'tags': tags,
        'current_tag': tag_slug,
        'search_query': search_query,
        'paginator': paginator,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages()
    })

def news_detail(request, slug):
    """Отображение детальной страницы новости"""
    post = get_object_or_404(Newspost, slug=slug)
    tags = Tag.objects.all()
    
    # Get comments for this news post
    content_type = ContentType.objects.get_for_model(Newspost)
    comments = Comment.objects.filter(content_type=content_type, object_id=post.id)
    
    # Prepare comment form
    comment_form = CommentForm()
    comment_form_action = f'/comments/newspost/{post.id}/comment/'
    
    # Get related posts with the same tags
    related_posts = Newspost.objects.filter(tags__in=post.tags.all()).exclude(id=post.id).distinct()[:3]
    
    context = {
        'post': post,
        'tags': tags,
        'related_posts': related_posts,
        'comments': comments,
        'comment_form': comment_form,
        'comment_form_action': comment_form_action,
    }
    
    return render(request, 'news_detail.html', context)

def liderplatform1(request):
    return render(request, 'liderplatform.html', {'experts': Expert.objects.all()})
    
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
    
def logout_view(request):
    logout(request)
    return redirect('startpage:home')

def liderplatform(request):
    from users.models import User  # Твоя кастомная модель!
    experts = Expert.objects.all()
    users_count = User.objects.count()  # Твои пользователи!
    return render(request, 'liderplatform.html', {
        'experts': experts,
        'users_count': users_count
    })
