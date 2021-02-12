from django.db import models

class Document(models.Model):
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    constituents = models.FileField(blank=True)
    gifts = models.FileField(blank=True)
    gifts_attr = models.FileField(blank=True)
