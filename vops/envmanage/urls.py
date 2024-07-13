from django.urls import path
from envmanage import views


urlpatterns = [
    path("envList/", views.env_list),
    #path("envChange/"),
    path("softList/",views.soft_list),
    #path("softInit/"),
]
