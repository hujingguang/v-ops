from django.urls import path
from usermanage import views
from common.auth import authenticate_entry, sign_out
from common.config import change_config


urlpatterns = [
    path('', views.index),
    path('login/', views.login, name='login'),
    path('logout/', sign_out),
    path('index/', views.index),
    path('dashboard/', views.dashboard),
    path('sysconfig/', views.sysconfig),
    path('sysconfig/change/', change_config),
    path('authenticate/', authenticate_entry),
]
