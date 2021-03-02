import os
import re

import numpy as np
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.shortcuts import get_object_or_404
import pandas as pd
from datetime import date

class Document(models.Model):
    registrations = models.FileField(upload_to='documents/')
    donations = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    constituents = models.FileField(blank=True)
    gifts = models.FileField(blank=True)
    gifts_attr = models.FileField(blank=True)

    def delete(self, *args, **kwargs):
        if os.path.isfile(self.registrations.path):
            os.remove(self.registrations.path)
        if os.path.isfile(self.registrations.path):
                os.remove(self.donations.path)
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

    def save(self, **kwargs):
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.float_format', '{:.0f}'.format)
        existing_constituents = pd.read_csv(self.document)
        for i, row in existing_constituents.iterrows():
            phone_number = row['Phone']
            if not isinstance(phone_number, float):
                cleaned_number = re.findall(r'[0-9]+', phone_number)
                if len(cleaned_number) > 1:
                    cleaned_number = ''.join(cleaned_number)
                elif len(cleaned_number) == 1:
                    cleaned_number = cleaned_number[0]
                else:
                    cleaned_number = np.nan
            existing_constituents.loc[i, 'Phone'] = cleaned_number
            print("Currently on row: {}; Currently iterrated {}% of rows".format(i, (i + 1) / len(existing_constituents.index) * 100))
        today = date.today()
        existing_constituents.to_csv("media/documents/ExistingConstituents/cleaned_constituents" + str(today) + ".csv")
        self.document = ("documents/ExistingConstituents/" + "cleaned_constituents" + str(today) + ".csv")
        super(ConstituentFile, self).save(**kwargs)

