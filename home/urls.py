from django.urls import path
from . import views
from Django_2021 import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.go_home, name = 'home'),
]
