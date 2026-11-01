from django.urls import path
from . import views


app_name = "users"
urlpatterns = [
    path('login/', views.LoginUser.as_view(), name='login'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('profile/', views.profile, name='profile'),
    path('profile/general/', views.profile_general, name='profile_general'),
    path('profile/security/', views.profile_security, name='profile_security'),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
]
