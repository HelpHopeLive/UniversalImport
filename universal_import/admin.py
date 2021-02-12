from django.contrib import admin
from django.contrib import admin
from .models import Document
import pandas as pd

class uploadAdmin(admin.ModelAdmin):  # add this
  list_display = ('document', 'constituents', 'gifts', 'gifts_attr')


# Register your models here.
admin.site.register(Document, uploadAdmin) # add this
# Register your models here.
