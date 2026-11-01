from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    # Список проектов
    path('', views.projects, name='projects'),

    # Мои проекты
    path('my-projects/', views.my_projects, name='my_projects'),

    # Создание проекта
    path('create/', views.create_project, name='create_project'),

    # Детальная страница проекта (по slug)
    path('project/<slug:project_slug>/', views.project_detail, name='project_detail'),

    # Редактирование проекта (по id)
    path('project/<int:project_id>/edit/', views.edit_project, name='edit_project'),

    # Удаление проекта (по id)
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),

    # Подача заявки в проект (по id проекта)
    path('project/<int:project_id>/apply/', views.project_application, name='project_application'),

    # Жалоба на проект (по id проекта)
    path('project/<int:project_id>/complaint/', views.project_complaint, name='project_complaint'),

    # Принять / отклонить заявку (по id заявки)
    path('application/<int:application_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:application_id>/reject/', views.reject_application, name='reject_application'),

    # Приглашения в проект (по id проекта или token)
    path('project/<int:project_id>/invite/', views.invite_member, name='invite_member'),
    path('invitations/accept/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('invitations/decline/<str:token>/', views.decline_invitation, name='decline_invitation'),
    path('invitations/verify/', views.verify_invitation, name='verify_invitation'),

    # Задачи
    path('project/<int:project_id>/tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    # Статические страницы футера
    path('liderplatform1/', views.liderplatform1, name='liderplatform1'),
    path('workshop1/', views.workshop1, name='workshop1'),
    path('documents1/', views.documents1, name='documents1'),
    path('shop1/', views.shop1, name='shop1'),
    path('service1/', views.service1, name='service1'),
    path('contact1/', views.contact1, name='contact1'),
    path('step1/', views.step1, name='step1'),
    path('step2/', views.step2, name='step2'),
    path('step3/', views.step3, name='step3'),
    path('step4/', views.step4, name='step4'),
    path('step5/', views.step5, name='step5'),
    
    path('project/<int:project_id>/removeteammember/<int:user_id>/', views.removeteammember, name='removeteammember'),
    path('project/<slug:project_slug>/certificate/', views.project_certificate, name="project_certificate"),


]
