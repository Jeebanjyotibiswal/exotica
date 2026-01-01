# Admin/views.py
# Admin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from Home.models import StudentRegistration, Event, DynamicCategory  # ADD DynamicCategory here
from django.db.models import Q, Count
import csv
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
from .models import Result, Announcment, MrMissNit  # Import all models
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@never_cache
@login_required(login_url='admin_login')
def admin_dashboard(request):
    """
    Admin dashboard view showing all participants
    """
    # Get all participants with event information
    all_data = StudentRegistration.objects.all().select_related('event')
    
    # Get all events for dropdowns
    events = Event.objects.all()
    
    context = {
        'all_data': all_data,
        'events': events,
    }
    return render(request, 'Admin/admin.html', context)

@login_required
def add_participant(request):
    """
    Add new participant from admin dashboard
    """
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            regd_no = request.POST.get('regd_no')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            branch = request.POST.get('branch')
            year = request.POST.get('year')
            event_id = request.POST.get('event')
            
            # Validate required fields
            if not all([name, regd_no, phone, email, branch, year, event_id]):
                messages.error(request, "All fields are required!")
                return redirect('admin_dashboard')
            
            # Get event instance
            event = get_object_or_404(Event, id=event_id)
            
            # Check if registration number already exists
            if StudentRegistration.objects.filter(regd_no=regd_no).exists():
                messages.error(request, f"Registration number {regd_no} already exists!")
                return redirect('admin_dashboard')
            
            # Create new participant
            participant = StudentRegistration.objects.create(
                name=name,
                regd_no=regd_no,
                phone=phone,
                email=email,
                branch=branch,
                year=year,
                event=event
            )
            
            messages.success(request, f'Participant {name} added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding participant: {str(e)}')
            return redirect('admin_dashboard')
    
    # If not POST, redirect to dashboard
    return redirect('admin_dashboard')

@login_required
def edit_participant(request, participant_id):
    """
    Edit existing participant
    """
    if request.method == 'POST':
        try:
            # Get participant
            participant = get_object_or_404(StudentRegistration, id=participant_id)
            
            # Update fields
            participant.name = request.POST.get('name')
            participant.regd_no = request.POST.get('regd_no')
            participant.phone = request.POST.get('phone')
            participant.email = request.POST.get('email')
            participant.branch = request.POST.get('branch')
            participant.year = request.POST.get('year')
            
            # Update event if provided
            event_id = request.POST.get('event')
            if event_id:
                event = Event.objects.get(id=event_id)
                participant.event = event
            
            participant.save()
            
            messages.success(request, f'Participant {participant.name} updated successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating participant: {str(e)}')
            return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@login_required
def delete_participant(request, participant_id):
    """
    Delete participant with AJAX support
    """
    if request.method == 'POST':
        try:
            participant = get_object_or_404(StudentRegistration, id=participant_id)
            participant_name = participant.name
            participant.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': f'Participant {participant_name} deleted successfully!'
                })
            else:
                messages.success(request, f'Participant {participant_name} deleted successfully!')
                return redirect('admin_dashboard')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error deleting participant: {str(e)}')
                return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@login_required
def export_participants(request):
    """
    Export filtered participants to CSV
    """
    # Get filter parameters from POST request
    search = request.POST.get('search', '').strip()
    branch = request.POST.get('branch', '').strip()
    event = request.POST.get('event', '').strip()
    
    # Start with all participants
    participants = StudentRegistration.objects.all().select_related('event')
    
    # Apply filters if provided
    if search:
        participants = participants.filter(
            Q(name__icontains=search) |
            Q(regd_no__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(branch__icontains=search) |
            Q(event__event_name__icontains=search)
        )
    
    if branch:
        participants = participants.filter(branch=branch)
    
    if event:
        participants = participants.filter(event__event_name=event)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="participants_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Write CSV with UTF-8 BOM for Excel compatibility
    response.write('\ufeff')
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Registration No', 'Phone', 'Email', 'Branch', 'Year', 'Event', 'Event Category', 'Registered At'])
    
    # Write data
    for participant in participants:
        writer.writerow([
            participant.id,
            participant.name,
            participant.regd_no,
            participant.phone,
            participant.email,
            participant.branch,
            participant.year,
            participant.event.event_name,
            participant.event.get_category_display(),
            participant.registered_at.strftime('%Y-%m-%d %H:%M:%S') if participant.registered_at else ''
        ])
    
    return response

@never_cache
@login_required(login_url='admin_login')
def event_management(request):
    """
    Event management view for admin with category management
    """
    # Get all events with participant count
    events_queryset = Event.objects.annotate(participants_count=Count('studentregistration')).order_by('category', 'event_name')
    
    # Calculate stats (from all events, not just paginated ones)
    total_events = events_queryset.count()
    active_events = events_queryset.filter(is_active=True).count()
    total_registrations = sum(event.participants_count for event in events_queryset)
    
    # Pagination - show 10 events per page
    page = request.GET.get('page', 1)
    paginator = Paginator(events_queryset, 10)
    
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)
    
    # Get category choices from the model (default categories)
    category_choices = dict(Event.CATEGORY_CHOICES)
    
    # Get dynamic categories from database
    dynamic_categories = DynamicCategory.objects.filter(is_active=True)
    
    # Combine default and dynamic categories
    all_categories_list = list(Event.CATEGORY_CHOICES)  # Start with default choices
    
    # Add dynamic categories to the list
    for cat in dynamic_categories:
        all_categories_list.append((cat.code, cat.name))
    
    # Create existing_categories list for display
    existing_categories = []
    
    # Add default categories
    for code, name in Event.CATEGORY_CHOICES:
        existing_categories.append({
            'code': code,
            'name': name,
            'is_default': True
        })
    
    # Add dynamic categories
    for cat in dynamic_categories:
        existing_categories.append({
            'code': cat.code,
            'name': cat.name,
            'is_default': False,
            'id': cat.id  # For reference
        })
    
    context = {
        'events': events,  # This is now a paginated object
        'existing_categories': existing_categories,
        'all_categories': all_categories_list,  # This includes both default and dynamic
        'total_events': total_events,
        'active_events': active_events,
        'total_registrations': total_registrations,
    }
    return render(request, 'Admin/event_management.html', context)

@login_required
@require_http_methods(["POST"])
def add_event(request):
    """
    Add new event with simplified details
    """
    try:
        # Get only required form data
        event_name = request.POST.get('event_name', '').strip()
        category = request.POST.get('category', '').strip()
        rules = request.POST.get('rules', '').strip()
        max_participants = request.POST.get('max_participants', '1').strip()
        team_size = request.POST.get('team_size', '').strip()
        duration = request.POST.get('duration', '').strip()
        registration_deadline = request.POST.get('registration_deadline', '').strip()
        is_active = request.POST.get('is_active', 'on') == 'on'
        
        # Simple validation
        if not event_name:
            messages.error(request, 'Event name is required!')
            return redirect('event_management')
        
        if not category:
            messages.error(request, 'Event category is required!')
            return redirect('event_management')
        
        # Check if event already exists
        if Event.objects.filter(event_name__iexact=event_name).exists():
            messages.error(request, f'Event "{event_name}" already exists!')
            return redirect('event_management')
        
        # Create event with simplified details
        event = Event.objects.create(
            event_name=event_name,
            category=category,
            rules=rules,
            max_participants=int(max_participants) if max_participants.isdigit() else 1,
            team_size=team_size,
            duration=duration,
            registration_deadline=registration_deadline if registration_deadline else None,
            is_active=is_active,
            description=f"{event_name} - {dict(Event.CATEGORY_CHOICES).get(category, category)} Event"
        )
        
        messages.success(request, f'Event "{event_name}" added successfully!')
        return redirect('event_management')
        
    except Exception as e:
        messages.error(request, f'Error adding event: {str(e)}')
        return redirect('event_management')

@login_required
def edit_event(request, event_id):
    """
    Edit existing event - CORRECTED VERSION (only one)
    """
    if request.method == 'GET':
        # Return event data for editing
        try:
            event = get_object_or_404(Event, id=event_id)
            return JsonResponse({
                'success': True,
                'event': {
                    'id': event.id,
                    'event_name': event.event_name,
                    'category': event.category,
                    'rules': event.rules or '',
                    'max_participants': event.max_participants,
                    'team_size': event.team_size or '',
                    'duration': event.duration or '',
                    'registration_deadline': event.registration_deadline.strftime('%Y-%m-%dT%H:%M') if event.registration_deadline else '',
                    'is_active': event.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    elif request.method == 'POST':
        try:
            event = get_object_or_404(Event, id=event_id)
            
            # Get only required form data
            event_name = request.POST.get('event_name')
            category = request.POST.get('category')
            rules = request.POST.get('rules', '').strip()
            max_participants = request.POST.get('max_participants', '1').strip()
            team_size = request.POST.get('team_size', '').strip()
            duration = request.POST.get('duration', '').strip()
            registration_deadline = request.POST.get('registration_deadline', '').strip()
            is_active = request.POST.get('is_active', 'on') == 'on'
            
            if not event_name or not category:
                messages.error(request, "Event name and category are required!")
                return redirect('event_management')
            
            # Check if another event with the same name exists (excluding current event)
            if Event.objects.filter(event_name__iexact=event_name).exclude(id=event_id).exists():
                messages.error(request, f'Event with name "{event_name}" already exists!')
                return redirect('event_management')
            
            # Update event with simplified fields
            event.event_name = event_name
            event.category = category
            event.rules = rules
            event.max_participants = int(max_participants) if max_participants.isdigit() else 1
            event.team_size = team_size
            event.duration = duration
            event.registration_deadline = registration_deadline if registration_deadline else None
            event.is_active = is_active
            event.save()
            
            messages.success(request, f'Event "{event.event_name}" updated successfully!')
            return redirect('event_management')
            
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
            return redirect('event_management')

# Admin/views.py - Update the delete_event function
@login_required
def delete_event(request, event_id):
    """
    Delete event with AJAX support
    """
    if request.method == 'POST':
        try:
            event = get_object_or_404(Event, id=event_id)
            event_name = event.event_name
            
            # Check if event has participants
            if event.studentregistration_set.exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'error': f'Cannot delete event "{event_name}" because it has participants!'
                    })
                else:
                    messages.error(request, f'Cannot delete event "{event_name}" because it has participants!')
                    return redirect('event_management')
            
            event.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': f'Event "{event_name}" deleted successfully!'
                })
            else:
                messages.success(request, f'Event "{event_name}" deleted successfully!')
                return redirect('event_management')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error deleting event: {str(e)}')
                return redirect('event_management')
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@require_http_methods(["POST"])
def manage_event_category(request):
    """
    Add or remove event categories
    """
    try:
        action = request.POST.get('action')
        
        if action == 'add_category':
            category_name = request.POST.get('category_name', '').strip().upper()
            display_name = request.POST.get('display_name', '').strip()
            
            if not category_name or not display_name:
                messages.error(request, 'Category name and display name are required!')
                return redirect('event_management')
            
            # Check if category already exists
            existing_categories = Event.objects.values_list('category', flat=True).distinct()
            if category_name in existing_categories:
                messages.error(request, f'Category "{category_name}" already exists!')
                return redirect('event_management')
            
            # Note: Since categories are defined in model choices, we can't dynamically add them
            # We'll store this separately and update the form options
            messages.success(request, f'Note: To add new categories, update the Event model in models.py')
            return redirect('event_management')
            
        elif action == 'remove_category':
            category_code = request.POST.get('category_code')
            
            # Check if any events use this category
            events_with_category = Event.objects.filter(category=category_code).exists()
            if events_with_category:
                messages.error(request, f'Cannot remove category! There are events using this category.')
                return redirect('event_management')
            
            messages.success(request, f'Category removed successfully!')
            return redirect('event_management')
            
    except Exception as e:
        messages.error(request, f'Error managing category: {str(e)}')
        return redirect('event_management')

def admin_logout(request):
    """
    Admin logout view
    """
    logout(request)
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

# RESULT MANAGEMENT FUNCTIONS

def upload_result(request):
    """
    Upload new result or edit existing result
    """
    if request.method == "POST":
        try:
            # Check if editing existing result
            result_id = request.POST.get('result_id')
            
            if result_id:
                # Edit existing result
                result = get_object_or_404(Result, id=result_id)
                
                # Update fields
                result.winner = request.POST.get("Winner")
                result.game = request.POST.get("event")
                result.branch = request.POST.get("Branch")
                result.position = request.POST.get("position")
                
                # Update featured status
                featured = request.POST.get("featured")
                current_featured = result.featured
                new_featured = True if featured == "on" else False
                
                # Check if trying to feature and already have 3 featured
                if not current_featured and new_featured:
                    featured_count = Result.objects.filter(featured=True).count()
                    if featured_count >= 3:
                        messages.error(request, "❌ Only 3 winners can be featured on the home page! Please unfeature another winner first.")
                        return redirect('upload-result')
                
                result.featured = new_featured
                
                # Update photo only if new one is provided
                image = request.FILES.get("Image")
                if image:
                    result.photo = image
                
                result.save()
                messages.success(request, "✅ Result updated successfully")
                
            else:
                # Create new result
                winner = request.POST.get("Winner")
                event = request.POST.get("event")
                branch = request.POST.get("Branch")
                position = request.POST.get("position")
                image = request.FILES.get("Image")
                
                # Get featured status
                featured = request.POST.get("featured")
                is_featured = True if featured == "on" else False
                
                # Check if trying to feature and already have 3 featured
                if is_featured:
                    featured_count = Result.objects.filter(featured=True).count()
                    if featured_count >= 3:
                        messages.error(request, "❌ Only 3 winners can be featured on the home page! Please unfeature another winner first.")
                        return redirect('upload-result')
                
                # Create new result
                result = Result(
                    winner=winner,
                    branch=branch,
                    position=position,
                    game=event,
                    photo=image,
                    featured=is_featured
                )
                result.save()
                messages.success(request, "✅ Result uploaded successfully")
            
            return redirect('upload-result')
            
        except ValidationError as e:
            messages.error(request, f"❌ {e}")
            return redirect('upload-result')
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
            return redirect('upload-result')
    
    # GET request - show all results
    results = Result.objects.all().order_by('-id')
    featured_count = Result.objects.filter(featured=True).count()
    
    # Check if editing a specific result
    result_id = request.GET.get('edit')
    result = None
    if result_id:
        try:
            result = get_object_or_404(Result, id=result_id)
        except:
            pass
    
    context = {
        'results': results,
        'result': result,  # This will be None if not editing
        'featured_count': featured_count,
    }
    return render(request, "Admin/upload_result.html", context)

def edit_result(request, result_id):
    """
    Edit existing result - redirects to upload_result with edit parameter
    """
    # Redirect to upload_result with edit parameter
    return redirect(f'/admin-panel/upload-result/?edit={result_id}')

def delete_result(request, result_id):
    """
    Delete result
    """
    if request.method == "POST":
        try:
            result = get_object_or_404(Result, id=result_id)
            winner_name = result.winner
            result.delete()
            messages.success(request, f"✅ Result for {winner_name} deleted successfully")
        except Exception as e:
            messages.error(request, f"❌ Error deleting result: {str(e)}")
    
    return redirect('upload-result')

def toggle_featured(request, result_id):
    """
    Toggle featured status of a result with 3-limit check
    """
    if request.method == 'POST':
        try:
            result = get_object_or_404(Result, id=result_id)
            
            # Check current status
            current_featured = result.featured
            
            # If trying to feature and already have 3 featured
            if not current_featured:
                featured_count = Result.objects.filter(featured=True).count()
                if featured_count >= 3:
                    messages.error(request, "❌ Only 3 winners can be featured on the home page! Please unfeature another winner first.")
                    return redirect('upload-result')
            
            # Toggle featured status
            result.featured = not current_featured
            result.save()
            
            if result.featured:
                messages.success(request, f'✅ {result.winner} is now featured on home page!')
            else:
                messages.success(request, f'✅ {result.winner} is no longer featured.')
                
        except ValidationError as e:
            messages.error(request, f"❌ {e}")
        except Exception as e:
            messages.error(request, f'❌ Error toggling featured status: {str(e)}')
    
    return redirect('upload-result')

# ANNOUNCEMENT FUNCTIONS

@login_required
def announcment_view(request):
    # Fetch only the last 5 announcements
    announcements = Announcment.objects.all().order_by('-created_at')[:5]
    
    # Check if editing an announcement
    edit_id = request.GET.get('edit')
    edit_announcement = None
    
    if request.method == 'POST':
        if 'post_announcement' in request.POST:
            # Create new announcement
            title = request.POST.get('title')
            content = request.POST.get('body')
            attachment = request.FILES.get('notice')
            
            announcement = Announcment(
                title=title,
                content=content,
                attatchment=attachment
            )
            announcement.save()
            
            messages.success(request, 'Announcement created successfully!')
            return redirect('announcment')
            
        elif 'update_announcement' in request.POST:
            # Update existing announcement
            edit_id = request.POST.get('edit_id')
            if edit_id:
                return edit_announcement(request, edit_id)
    
    # Check if we're editing via URL parameter
    elif edit_id:
        try:
            edit_announcement = Announcment.objects.get(id=edit_id)
        except Announcment.DoesNotExist:
            pass
    
    return render(request, 'Admin/announcment.html', {
        'announcements': announcements,
        'edit_announcement': edit_announcement
    })

@login_required
def delete_announcement(request, announcement_id):
    """Delete a single announcement"""
    if request.method == 'POST':
        try:
            announcement = get_object_or_404(Announcment, id=announcement_id)
            announcement_title = announcement.title
            announcement.delete()
            
            messages.success(request, f'Announcement "{announcement_title}" deleted successfully!')
            return redirect('announcment')
            
        except Exception as e:
            messages.error(request, f'Error deleting announcement: {str(e)}')
            return redirect('announcment')
    
    return redirect('announcment')

@login_required
def clear_all_announcements(request):
    """Delete all announcements"""
    if request.method == 'POST':
        try:
            count = Announcment.objects.count()
            Announcment.objects.all().delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'All {count} announcements deleted successfully!'
                })
            else:
                messages.success(request, f'All {count} announcements deleted successfully!')
                return redirect('announcment')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error clearing announcements: {str(e)}')
                return redirect('announcment')
    
    return redirect('announcment')

@login_required
def edit_announcement(request, announcement_id):
    """Edit an existing announcement"""
    announcement = get_object_or_404(Announcment, id=announcement_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            content = request.POST.get('body')
            attachment = request.FILES.get('notice')
            
            # Update announcement
            announcement.title = title
            announcement.content = content
            
            # Update attachment only if new one is provided
            if attachment:
                announcement.attatchment = attachment
            
            announcement.save()
            
            messages.success(request, 'Announcement updated successfully!')
            return redirect('announcment')
            
        except Exception as e:
            messages.error(request, f'Error updating announcement: {str(e)}')
            return redirect('announcment')
    
    # GET request - show edit form
    announcements = Announcment.objects.all().order_by('-created_at')[:5]
    
    context = {
        'edit_announcement': announcement,
        'announcements': announcements,
    }
    return render(request, 'Admin/announcment.html', context)

# MR & MISS NIT FUNCTIONS

@login_required(login_url='admin_login')
def mr_miss_nit_management(request):
    """
    Admin panel for managing Mr & Miss NIT content
    """
    # Get the latest or create new
    try:
        mr_miss_nit = MrMissNit.objects.latest('year')
    except MrMissNit.DoesNotExist:
        mr_miss_nit = None
    
    if request.method == 'POST':
        year = request.POST.get('year')
        mr_name = request.POST.get('mr_name')
        mr_photo = request.FILES.get('mr_photo')
        mr_department = request.POST.get('mr_department')
        mr_description = request.POST.get('mr_description', '')
        
        miss_name = request.POST.get('miss_name')
        miss_photo = request.FILES.get('miss_photo')
        miss_department = request.POST.get('miss_department')
        miss_description = request.POST.get('miss_description', '')
        
        event_description = request.POST.get('event_description', '').strip()
        judging_criteria = request.POST.get('judging_criteria', '').strip()
        
        if mr_miss_nit:
            # Update existing
            mr_miss_nit.year = year
            mr_miss_nit.mr_name = mr_name
            if mr_photo:
                mr_miss_nit.mr_photo = mr_photo
            mr_miss_nit.mr_department = mr_department
            mr_miss_nit.mr_description = mr_description
            
            mr_miss_nit.miss_name = miss_name
            if miss_photo:
                mr_miss_nit.miss_photo = miss_photo
            mr_miss_nit.miss_department = miss_department
            mr_miss_nit.miss_description = miss_description
            
            # Preserve line breaks in text fields
            mr_miss_nit.event_description = event_description
            mr_miss_nit.judging_criteria = judging_criteria
            
            mr_miss_nit.save()
            messages.success(request, 'Mr & Miss NIT content updated successfully!')
        else:
            # Create new
            MrMissNit.objects.create(
                year=year,
                mr_name=mr_name,
                mr_photo=mr_photo,
                mr_department=mr_department,
                mr_description=mr_description,
                miss_name=miss_name,
                miss_photo=miss_photo,
                miss_department=miss_department,
                miss_description=miss_description,
                event_description=event_description,
                judging_criteria=judging_criteria
            )
            messages.success(request, 'Mr & Miss NIT content created successfully!')
        
        return redirect('mr_miss_nit_management')
    
    context = {
        'mr_miss_nit': mr_miss_nit,
    }
    return render(request, 'Admin/mr_miss_nit_management.html', context)
@login_required
@require_http_methods(["POST"])
def add_event_category(request):
    """
    Add new event category dynamically - UPDATED TO USE DATABASE
    """
    try:
        display_name = request.POST.get('display_name', '').strip()
        category_code = request.POST.get('category_code', '').strip().upper()
        
        if not display_name:
            messages.error(request, 'Category name is required!')
            return redirect('event_management')
        
        # Generate code from name if not provided
        if not category_code:
            category_code = display_name.upper().replace(' ', '_').replace('-', '_')
            # Remove any non-alphanumeric characters
            category_code = ''.join(c for c in category_code if c.isalnum() or c == '_')
        
        # Check if category already exists in DynamicCategory
        if DynamicCategory.objects.filter(code=category_code).exists():
            messages.error(request, f'Category code "{category_code}" already exists!')
            return redirect('event_management')
        
        # Check if category already exists in default choices
        default_cats = dict(Event.CATEGORY_CHOICES)
        if category_code in default_cats:
            messages.error(request, f'Category code "{category_code}" is a default category!')
            return redirect('event_management')
        
        # Create new dynamic category
        DynamicCategory.objects.create(
            code=category_code,
            name=display_name,
            is_active=True
        )
        
        messages.success(request, f'Category "{display_name}" added successfully!')
        
    except Exception as e:
        messages.error(request, f'Error adding category: {str(e)}')
    
    return redirect('event_management')

@login_required
@require_http_methods(["POST"])
def edit_event_category(request):
    """
    Edit existing event category - UPDATED TO USE DATABASE
    """
    try:
        old_code = request.POST.get('old_code', '').strip()
        new_display_name = request.POST.get('new_display_name', '').strip()
        
        if not old_code or not new_display_name:
            messages.error(request, 'Category code and display name are required!')
            return redirect('event_management')
        
        # Check if it's a default category
        default_cats = dict(Event.CATEGORY_CHOICES)
        if old_code in default_cats:
            messages.info(request, 'Default categories can only be edited in models.py')
            return redirect('event_management')
        
        # Find and update in DynamicCategory
        try:
            category = DynamicCategory.objects.get(code=old_code)
            category.name = new_display_name
            category.save()
            messages.success(request, f'Category updated to "{new_display_name}"!')
        except DynamicCategory.DoesNotExist:
            messages.error(request, 'Category not found!')
        
    except Exception as e:
        messages.error(request, f'Error editing category: {str(e)}')
    
    return redirect('event_management')

@login_required
@require_http_methods(["POST"])
def delete_event_category(request):
    """
    Delete event category and update affected events - UPDATED TO USE DATABASE
    """
    try:
        category_code = request.POST.get('category_code', '').strip()
        
        if not category_code:
            messages.error(request, 'Category code is required!')
            return redirect('event_management')
        
        # Don't allow deleting LITERARY (default category)
        default_cats = dict(Event.CATEGORY_CHOICES)
        if category_code in default_cats:
            messages.error(request, f'Cannot delete default "{default_cats[category_code]}" category!')
            return redirect('event_management')
        
        # Check if category exists in DynamicCategory
        try:
            category = DynamicCategory.objects.get(code=category_code)
            
            # Check if any events use this category
            events_count = Event.objects.filter(category=category_code).count()
            
            if events_count > 0:
                # Update all events with this category to LITERARY
                Event.objects.filter(category=category_code).update(category='LITERARY')
                messages.warning(request, 
                    f'{events_count} event(s) moved to LITERARY category.')
            
            # Delete the dynamic category
            category_name = category.name
            category.delete()
            
            messages.success(request, f'Category "{category_name}" deleted successfully!')
            
        except DynamicCategory.DoesNotExist:
            messages.error(request, 'Category not found!')
        
    except Exception as e:
        messages.error(request, f'Error deleting category: {str(e)}')
    
    return redirect('event_management')