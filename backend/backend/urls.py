"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from core import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.landing, name='landing'),
    path('signup/', views.signup, name='signup'),
    #path('tags/', views.tags, name='tags'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Django auth
    path(
        'accounts/login/',
        LoginView.as_view(template_name='login.html'),
        name='login'
    ),
    path(
        'accounts/logout/',
        LogoutView.as_view(template_name='logout.html'),
        name='logout'
    ),
    path('api/posts/', views.get_posts, name='get_posts'),
    path('api/posts/create/', views.create_post, name='create_post'),
    path('api/posts/<int:post_id>/reply/', views.add_reply, name='add_reply'),
    path('api/posts/<int:post_id>/react/', views.add_reaction, name='add_reaction'),
    path('insights/', views.insights_view, name='insights'),
    path('notifications/', views.notifications_view, name='notifications'),

    # Custom Admin Panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/insights/', views.manage_insights, name='manage_insights'),
    path('admin-panel/insights/delete/<int:insight_id>/', views.delete_insight, name='delete_insight'),
    path('admin-panel/notifications/', views.manage_notifications, name='manage_notifications'),
    path('admin-panel/notifications/delete/<int:notif_id>/', views.delete_notification, name='delete_notification'),
    path('admin-panel/posts/', views.manage_posts, name='manage_posts'),
    path('admin-panel/posts/delete/<int:post_id>/', views.delete_post, name='delete_post'),
]