from django import forms
from universal_import.models import Document
from.convert import convert
from .models import ConstituentFile


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('document', 'constituents', 'gifts', 'gifts_attr')
    def save(self, commit=True):
        m = super(DocumentForm, self).save(commit=False)
        output_files = convert(self.instance.document)
        self.instance.constituents = ("documents/" + output_files[0])
        self.instance.gifts = ("documents/" + output_files[1])
        self.instance.gifts_attr = ("documents/" + output_files[2])
        if commit:
            m.save()
        return m

