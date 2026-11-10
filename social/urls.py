
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('create-post/', views.create_post, name='create_post'),
    path('like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('profile/', views.profile, name='profile'),
    path('users/<str:username>/', views.user_profile, name='user_profile'),
    path('users/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('inbox/', views.inbox, name='inbox'),
    path('chat/<str:username>/', views.chat, name='chat'),
    path('notifications/', views.notifications, name='notifications'),
]
