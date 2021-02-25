import os

from django.core.exceptions import FieldDoesNotExist
from django.db import models

class Document(models.Model):
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    constituents = models.FileField(blank=True)
    gifts = models.FileField(blank=True)
    gifts_attr = models.FileField(blank=True)

    def delete(self, *args, **kwargs):
        if os.path.isfile(self.document.path):
            os.remove(self.document.path)

        super(Document, self).delete(*args, **kwargs)


class TeamManager(models.Manager):
    def create_team(self, number, title, leader, fund_id):
        team = self.create(number=number, title=title, leader=leader, fund_id=fund_id)
        return team



class Team(models.Model):
    number = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    leader = models.CharField(max_length=100)
    fund_id = models.CharField(max_length=100)
    objects = TeamManager()


class ConstituentFile(models.Model):
    document = models.FileField(upload_to='documents/ExistingConstituents/')
    #team = Team.objects.create_team("1","test team", "zach hansen", "HHL25")


