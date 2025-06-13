from django.contrib import admin
from django.urls import path, include
from procoreapi import views
from procoreapi.views import CustomPasswordResetView, CustomPasswordResetConfirmView
from django.views.generic.base import TemplateView
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

urlpatterns = [
    path('login/', views.email_login_view, name='login'),
    path('admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('signup/', views.signup_view, name='signup'),
    path('procoreapi/', include('procoreapi.urls')),
    # path('accounts/', include('accounts.urls')),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('logout/', auth_views.LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
    # Password reset links
    path('password_reset/',
         CustomPasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html', # ensure this template exists
             subject_template_name='registration/password_reset_subject.txt', # ensure this exists
             success_url=reverse_lazy('password_reset_done'),
             # Optionally set from_email here if not done in settings or if you want to be sure
             # from_email='your_verified_smtp2go_email@example.com',
         ),
         name='password_reset'),

    path(
        'reset/<uidb64>/<token>/',
        CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]

