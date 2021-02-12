from django.urls import path, re_path
from . import views
from Django_2021 import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.model_form_upload, name='upload'),
    path('', views.model_form_download, name ='download'),
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)