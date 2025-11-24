from django.shortcuts import render

# Create your views here.
def home_view(request):
    return render(request, 'index.html')
def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')
    
def events_view(request):
    return render(request, 'events.html')
    
def gallery_view(request):
    return render(request, 'gallery.html')

def mr_miss_nit_view(request):
    return render(request, 'mr-miss-nit.html')

def registration_view(request):
    return render(request, 'registration.html')
