from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404

from universal_import.forms import DocumentForm, ConstituentForm
from universal_import.models import Document,ConstituentFile


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


def constituent_form_upload(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'POST':
            form = ConstituentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                #redirect to loading screen
                return redirect('/')
        else:
            form = ConstituentForm()
        return render(request, 'constituent_upload.html', {
            'form' : form
        })
    else:
        return render(request, 'login_error.html')

