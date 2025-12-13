# Home/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Event, StudentRegistration
from Admin.models import Result  # IMPORT FROM ADMIN APP

def home_view(request):
    # Latest 3 winners who are in 1st position
    winners = Result.objects.filter(position="1st").order_by('-id')[:3]
    
    context = {
        'winners': winners,
    }
    return render(request, 'index.html', context)

@never_cache
def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("admin_dashboard")
        else:
            return render(request, "admin_login.html", {"error_message": "Invalid username or password."})
    
    return render(request, "admin_login.html")

def about_view(request):
    return render(request, 'about.html')

def test_static(request):
    return render(request, 'test_static.html')

def register(request):
    # Get all events grouped by category
    events_by_category = {}
    for category_code, category_name in Event.CATEGORY_CHOICES:
        events = Event.objects.filter(category=category_code).order_by('event_name')
        if events.exists():
            events_by_category[category_name] = events
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        regd_no = request.POST.get('regd_no')
        branch = request.POST.get('branch')
        year = request.POST.get('year')
        event_id = request.POST.get('event')
        
        # Basic validation
        required_fields = [name, email, phone, regd_no, branch, year, event_id]
        if not all(required_fields):
            messages.error(request, "All fields are required!")
            return render(request, 'register.html', {'events_by_category': events_by_category})
        
        try:
            event = Event.objects.get(id=event_id)
            
            # Save to database
            registration = StudentRegistration(
                name=name,
                email=email,
                phone=phone,
                regd_no=regd_no,
                branch=branch,
                year=year,
                event=event
            )
            registration.save()
            
            # Prepare context for success page
            success_context = {
                'student_name': name,
                'event_name': event.event_name,
                'regd_no': regd_no,
                'branch': registration.get_branch_display(),
                'year': year,
                'email': email,
                'phone': phone,
                'registration_id': registration.id,
                'registered_at': registration.registered_at,
            }
            
            # Render the success page with context
            return render(request, 'registration_successfull.html', success_context)
            
        except Event.DoesNotExist:
            messages.error(request, "Invalid event selected!")
            return render(request, 'register.html', {'events_by_category': events_by_category})
    
    # GET request - show registration form
    return render(request, 'register.html', {'events_by_category': events_by_category})

def event_view(request):
    return render(request, 'events.html')

def mr_miss_nit_view(request):
    return render(request, 'mr-miss-nit.html')

def home_view(request):
    # Show ONLY 3 featured winners (admin selects which ones)
    winners = Result.objects.filter(featured=True).order_by('-id')[:3]
    
    context = {
        'winners': winners,
    }
    return render(request, 'index.html', context)

def all_winners_view(request):
    # Get position filter from URL
    position_filter = request.GET.get('position', 'all')
    
    # Get all winners
    if position_filter == 'all':
        winners = Result.objects.all().order_by('position', '-created_at')
    else:
        winners = Result.objects.filter(position=position_filter).order_by('-created_at')
    
    context = {
        'winners': winners,
        'current_filter': position_filter,
    }
    return render(request, 'all_winners.html', context)

def notice_view(request):
    from Admin.models import Announcment
    announcements = Announcment.objects.all().order_by('-created_at')[:6]
    # announcements = Announcment.objects.all().order_by('-created_at')[:5]
    context = {
        'announcements': announcements,
    }
    return render(request, 'notice.html', context)