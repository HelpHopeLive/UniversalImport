from django.shortcuts import render
# Create your views here.
def go_home(request):
    if request.method:
        return render(request, 'home.html')
