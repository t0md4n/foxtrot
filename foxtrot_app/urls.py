from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mailchimp/', views.mailchimp, name='mailchimp'),
    path('sharepoint/', views.sharepoint, name='sharepoint'),
    path('excel_upload/', views.excel_upload, name='excel_upload'),
    path('result/', views.result, name='result'),
    path('login/', views.login_view, name='login'),
]
