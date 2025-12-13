# Admin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from Home.models import StudentRegistration, Event
from django.db.models import Q, Count
import csv
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
from .models import Result  # Import Result model from Admin app
from django.core.exceptions import ValidationError

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
            Q(event_event_name_icontains=search)
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
    Event management view for admin
    """
    # Get all events with participant count
    events = Event.objects.annotate(participants_count=Count('studentregistration'))
    
    context = {
        'events': events,
    }
    return render(request, 'Admin/event_management.html', context)

@login_required
@require_http_methods(["POST"])
def add_event(request):
    """
    Add new event - SIMPLIFIED (only name and category)
    """
    try:
        # Get event name and category from POST data
        event_name = request.POST.get('event_name', '').strip()
        category = request.POST.get('category', '').strip()
        
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
        
        # Create event - ONLY name and category
        event = Event.objects.create(
            event_name=event_name,
            category=category
        )
        
        messages.success(request, f'Event "{event_name}" added successfully!')
        return redirect('event_management')
        
    except Exception as e:
        messages.error(request, f'Error adding event: {str(e)}')
        return redirect('event_management')

@login_required
def edit_event(request, event_id):
    """
    Edit existing event
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
                    'category': event.category
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    elif request.method == 'POST':
        try:
            event = get_object_or_404(Event, id=event_id)
            
            event_name = request.POST.get('event_name')
            category = request.POST.get('category')
            
            if not event_name or not category:
                messages.error(request, "Event name and category are required!")
                return redirect('event_management')
            
            # Check if another event with the same name exists (excluding current event)
            if Event.objects.filter(event_name__iexact=event_name).exclude(id=event_id).exists():
                messages.error(request, f'Event with name "{event_name}" already exists!')
                return redirect('event_management')
            
            # Update event
            event.event_name = event_name
            event.category = category
            event.save()
            
            messages.success(request, f'Event "{event.event_name}" updated successfully!')
            return redirect('event_management')
            
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
            return redirect('event_management')

@login_required
def delete_event(request, event_id):
    """
    Delete event
    """
    if request.method == 'POST':
        try:
            event = get_object_or_404(Event, id=event_id)
            event_name = event.event_name
            
            # Check if event has participants
            if event.studentregistration_set.exists():
                messages.error(request, f'Cannot delete event "{event_name}" because it has participants!')
                return redirect('event_management')
            
            event.delete()
            
            messages.success(request, f'Event "{event_name}" deleted successfully!')
            return redirect('event_management')
            
        except Exception as e:
            messages.error(request, f'Error deleting event: {str(e)}')
            return redirect('event_management')
    
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
from .models import Announcment

# In views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Announcment

def announcment_view(request):
    # Fetch only the last 5 announcements
    announcements = Announcment.objects.all().order_by('-created_at')[:5]
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('body')
        attatchment = request.FILES.get('notice')
        
        announcement = Announcment(
            title=title,
            content=content,
            attatchment=attatchment
        )
        announcement.save()
        
        messages.success(request, 'Announcement created successfully!')
        return redirect('announcment')
    
    return render(request, 'Admin/announcment.html', {
        'announcements': announcements
    })

from django.shortcuts import get_object_or_404
from django.http import JsonResponse

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