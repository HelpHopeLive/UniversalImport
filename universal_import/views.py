from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404

from universal_import.forms import DocumentForm
from universal_import.models import Document


def model_form_upload(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'POST':
            form = DocumentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('/download')
        else:
            form = DocumentForm()
        return render(request, 'model_form_upload.html', {
            'form': form
        })
    else:
        return render(request, 'login_error.html')


def model_form_download(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method:
            try:
                form = Document.objects.first()
            except Document.DoesNotExist:
                raise Http404("No Document matches the given query.")
        form.delete()
        return render(request, 'model_form_download.html', {
            'form': form
        })

    else:
        return render(request, 'login_error.html')

