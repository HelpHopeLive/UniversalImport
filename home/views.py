from django.shortcuts import render
# Create your views here.
def go_home(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method:
            return render(request, 'home.html')
    else:
        return render(request, 'login_error.html')