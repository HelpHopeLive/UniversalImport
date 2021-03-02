from django.contrib import admin
from django.contrib import admin
from .models import Document,Team, ConstituentFile

import pandas as pd

class uploadAdmin(admin.ModelAdmin):  # add this
  list_display = ('registrations', 'donations', 'constituents', 'gifts', 'gifts_attr')

class teamAdmin(admin.ModelAdmin):
  list_display = ('number', 'title', 'leader', 'fund_id')

class constituentFileAdmin(admin.ModelAdmin):
  list_display = ('document',)




# Register your models here.
admin.site.register(Document, uploadAdmin) # add this
admin.site.register(Team, teamAdmin) # add this
admin.site.register(ConstituentFile, constituentFileAdmin) # add this

# Register your models here.
