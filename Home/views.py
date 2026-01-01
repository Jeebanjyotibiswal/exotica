# Home/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Event, StudentRegistration, DynamicCategory
from Admin.models import Result, MrMissNit, Announcment

def home_view(request):
    # Show ONLY 3 featured winners (admin selects which ones)
    winners = Result.objects.filter(featured=True).order_by('-id')[:3]
    
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
    # Get all categories: default + dynamic
    all_categories = []
    
    # Add default categories from CATEGORY_CHOICES
    for category_code, category_name in Event.CATEGORY_CHOICES:
        all_categories.append({
            'code': category_code,
            'name': category_name,
            'is_default': True
        })
    
    # Add dynamic categories from database
    dynamic_categories = DynamicCategory.objects.filter(is_active=True)
    for cat in dynamic_categories:
        all_categories.append({
            'code': cat.code,
            'name': cat.name,
            'is_default': False
        })
    
    # Get all ACTIVE events grouped by category
    events_by_category = {}
    for cat in all_categories:
        events = Event.objects.filter(category=cat['code'], is_active=True).order_by('event_name')
        if events.exists():
            events_by_category[cat['name']] = events
    
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
            
            # Check if registration number already exists for this event
            if StudentRegistration.objects.filter(regd_no=regd_no, event=event).exists():
                messages.error(request, f"Registration number {regd_no} is already registered for this event!")
                return render(request, 'register.html', {'events_by_category': events_by_category})
            
            # ========== REMOVED PARTICIPANT LIMIT CHECK ==========
            # This block was removed:
            # current_participants = StudentRegistration.objects.filter(event=event).count()
            # if current_participants >= event.max_participants:
            #     messages.error(request, f"Event {event.event_name} has reached maximum participants!")
            #     return render(request, 'register.html', {'events_by_category': events_by_category})
            # =====================================================
            
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

# ========== ADD THIS MISSING FUNCTION ==========
def event_view(request):
    # Get all categories: default + dynamic
    all_categories = []
    
    # Add default categories from CATEGORY_CHOICES
    for category_code, category_name in Event.CATEGORY_CHOICES:
        all_categories.append({
            'code': category_code,
            'name': category_name,
            'is_default': True
        })
    
    # Add dynamic categories from database
    dynamic_categories = DynamicCategory.objects.filter(is_active=True)
    for cat in dynamic_categories:
        all_categories.append({
            'code': cat.code,
            'name': cat.name,
            'is_default': False
        })
    
    # Get all ACTIVE events grouped by category
    events_by_category = {}
    
    # Group events by category
    for cat in all_categories:
        # Get active events for this category
        events = Event.objects.filter(
            category=cat['code'], 
            is_active=True
        ).order_by('event_name')
        
        if events.exists():
            events_by_category[cat['name']] = events
    
    context = {
        'events_by_category': events_by_category,
    }
    return render(request, 'events.html', context)
# ===============================================

def mr_miss_nit_view(request):
    try:
        mr_miss_nit = MrMissNit.objects.latest('year')
    except MrMissNit.DoesNotExist:
        mr_miss_nit = None
    
    context = {
        'mr_miss_nit': mr_miss_nit,
    }
    return render(request, 'mr-miss-nit.html', context)

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
    announcements = Announcment.objects.all().order_by('-created_at')[:6]
    context = {
        'announcements': announcements,
    }
    return render(request, 'notice.html', context)