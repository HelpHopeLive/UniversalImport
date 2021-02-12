from django.urls import path
from . import views
from Django_2021 import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.model_form_upload, name = 'upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)