from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from functools import wraps
from .forms import SignupForm, AdminInsightForm, AdminNotificationForm, MentorInsightForm
from .models import Post, Reply, Reaction, Insight, Notification, Report, ANON_NAMES
import json, random

def staff_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            raise PermissionDenied("You do not have permission to access the admin panel.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ----------------- ADMIN PANEL -----------------

@staff_only
def admin_dashboard(request):
    notifications_count = Notification.objects.count()
    posts_count = Post.objects.count()
    reports_count = Report.objects.filter(is_resolved=False).count()
    return render(request, 'admin_dashboard.html', {
        'notifications_count': notifications_count,
        'posts_count': posts_count,
        'reports_count': reports_count
    })



@staff_only
def manage_notifications(request):
    notifications = Notification.objects.all().order_by('-timestamp')
    if request.method == 'POST':
        form = AdminNotificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_notifications')
    else:
        form = AdminNotificationForm()
    return render(request, 'admin_manage_notifications.html', {'notifications': notifications, 'form': form})

@staff_only
def delete_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    notif.delete()
    return redirect('manage_notifications')

@staff_only
def manage_posts(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'admin_manage_posts.html', {'posts': posts})

@staff_only
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect('manage_posts')

@staff_only
def manage_reports(request):
    reports = Report.objects.all().order_by('-created_at')
    return render(request, 'admin_manage_reports.html', {'reports': reports})

@staff_only
def delete_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.delete()
    return redirect('manage_reports')

@staff_only
def resolve_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.is_resolved = True
    report.save()
    return redirect('manage_reports')

# ----------------- TEMPLATES -----------------

def landing(request):
    return render(request, "landingpage.html")

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

def mentor_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'mentorprofile'):
                login(request, user)
                return redirect('mentor_panel')
            else:
                return render(request, 'mentor_login.html', {'error': 'Access denied: Your account does not have mentor privileges.'})
        else:
            return render(request, 'mentor_login.html', {'error': 'Invalid username or password'})
    return render(request, 'mentor_login.html')

@login_required
def dashboard(request):
    if hasattr(request.user, 'mentorprofile'):
        return redirect('mentor_panel')
    return render(request, 'discussion.html')


# ----------------- DISCUSSION API -----------------

@login_required
def get_posts(request):
    posts = Post.objects.all().order_by('-created_at')
    data = []
    user_reactions = Reaction.objects.filter(user=request.user).values_list('post_id', 'emoji')
    user_reaction_map = {}
    for pid, emoji in user_reactions:
        if pid not in user_reaction_map:
            user_reaction_map[pid] = []
        user_reaction_map[pid].append(emoji)

    for post in posts:
        # Aggregate reactions
        reactions_data = {}
        for r in post.reactions.all():
            reactions_data[r.emoji] = reactions_data.get(r.emoji, 0) + 1
            
        data.append({
            "id": post.id,
            "anon_name": post.anon_name,
            "content": post.content,
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "reactions": reactions_data,
            "user_reactions": user_reaction_map.get(post.id, []),
            "total_reactions": post.reactions.count(),
            "replies": [
                {
                    "id": reply.id,
                    "anon_name": reply.anon_name,
                    "content": reply.content,
                    "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M:%S")
                } for reply in post.replies.all().order_by('created_at')
            ]
        })
    return JsonResponse(data, safe=False)

@login_required
def create_post(request):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Content cannot be empty"}, status=400)
        post = Post.objects.create(
            author=request.user,
            anon_name=random.choice(ANON_NAMES),
            content=content
        )
        return JsonResponse({
            "id": post.id,
            "anon_name": post.anon_name,
            "content": post.content,
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return JsonResponse({"error": "Invalid request"}, status=405)

@login_required
def add_reply(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Content cannot be empty"}, status=400)
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
        reply = Reply.objects.create(
            post=post,
            author=request.user,
            anon_name=random.choice(ANON_NAMES),
            content=content
        )
        return JsonResponse({
            "id": reply.id,
            "anon_name": reply.anon_name,
            "content": reply.content,
            "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return JsonResponse({"error": "Invalid request"}, status=405)

@login_required
def add_reaction(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        emoji = data.get("emoji")
        if not emoji:
            return JsonResponse({"error": "Emoji required"}, status=400)
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
        
        reaction, created = Reaction.objects.get_or_create(post=post, user=request.user, emoji=emoji)
        if not created:
            reaction.delete()
            return JsonResponse({"success": True, "action": "removed", "emoji": emoji})
            
        return JsonResponse({"success": True, "action": "added", "emoji": emoji})
    return JsonResponse({"error": "Invalid request"}, status=405)

@login_required
def report_post(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        reason = data.get("reason", "").strip()
        if not reason:
            return JsonResponse({"error": "Reason cannot be empty"}, status=400)
        
        post = get_object_or_404(Post, id=post_id)
        Report.objects.create(post=post, reporter=request.user, reason=reason)
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=405)

@login_required
def insights_view(request):
    insights = Insight.objects.all().order_by('-created_at')
    return render(request, 'insight.html', {'insights': insights})

@login_required
def notifications_view(request):
    notifications = Notification.objects.all().order_by('-timestamp')
    unread_count = Notification.objects.filter(is_unread=True).count()
    return render(request, 'notification.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


# ----------------- MENTOR CHAT -----------------

@login_required
def user_mentor_chat(request, mentor_type):
    if mentor_type not in ['academic', 'emotional']:
        return redirect('dashboard')
    return render(request, 'chat.html', {'mentor_type': mentor_type})

@login_required
def mentor_panel(request):
    # Check if user is a mentor
    if not hasattr(request.user, 'mentorprofile'):
        return redirect('dashboard')
    
    mentor_type = request.user.mentorprofile.mentor_type

    # Handle Insight Form Submission
    if request.method == 'POST':
        form = MentorInsightForm(request.POST)
        if form.is_valid():
            insight = form.save(commit=False)
            insight.category = mentor_type
            insight.save()
            # Notify users after the insight is posted
            Notification.objects.create(
                title=f"New {mentor_type.capitalize()} Insight Available",
                content=f"A new insight '{insight.title}' has been uploaded by your {mentor_type} mentor.",
                image=insight.image
            )
            return redirect('mentor_panel')
    else:
        form = MentorInsightForm()

    # Get all users who have sent a message to this mentor type
    sessions = []
    from django.db.models import Max
    from .models import MentorMessage
    from django.contrib.auth.models import User
    
    # Find active sessions for this mentor type
    messages = MentorMessage.objects.filter(mentor_type=mentor_type)
    session_user_ids = messages.values_list('session_user', flat=True).distinct()
    
    for uid in session_user_ids:
        user = User.objects.get(id=uid)
        last_msg = messages.filter(session_user=user).order_by('-timestamp').first()
        unread_count = messages.filter(session_user=user, is_read=False).exclude(sender=request.user).count()
        sessions.append({
            'user': user,
            'last_message': last_msg,
            'unread_count': unread_count
        })
        
    # Sort by recent message
    sessions.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else None, reverse=True)
    
    return render(request, 'mentor_panel.html', {'sessions': sessions, 'mentor_type': mentor_type, 'form': form})

@login_required
def mentor_panel_chat(request, session_user_id, mentor_type):
    if not hasattr(request.user, 'mentorprofile') or request.user.mentorprofile.mentor_type != mentor_type:
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    session_user = get_object_or_404(User, id=session_user_id)
    return render(request, 'mentor_chat.html', {'session_user': session_user, 'mentor_type': mentor_type})

@login_required
def chat_api(request, session_user_id, mentor_type):
    from .models import MentorMessage
    from django.contrib.auth.models import User
    
    if request.method == "GET":
        messages = MentorMessage.objects.filter(session_user_id=session_user_id, mentor_type=mentor_type).order_by('timestamp')
        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        return JsonResponse(data, safe=False)
        
    elif request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Content cannot be empty"}, status=400)
            
        session_user = get_object_or_404(User, id=session_user_id)
        msg = MentorMessage.objects.create(
            session_user=session_user,
            sender=request.user,
            mentor_type=mentor_type,
            content=content
        )
        return JsonResponse({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

@login_required
def chat_notifications_api(request):
    from .models import MentorMessage
    data = {'unread_count': 0, 'sessions': []}
    
    if hasattr(request.user, 'mentorprofile'):
        # Mentor checking for messages from users
        mentor_type = request.user.mentorprofile.mentor_type
        unread = MentorMessage.objects.filter(mentor_type=mentor_type, is_read=False).exclude(sender=request.user)
        data['unread_count'] = unread.count()
    else:
        # User checking for messages from mentors
        unread = MentorMessage.objects.filter(session_user=request.user, is_read=False).exclude(sender=request.user)
        data['unread_count'] = unread.count()
        
    return JsonResponse(data)

@login_required
def mark_messages_read_api(request, session_user_id, mentor_type):
    from .models import MentorMessage
    if request.method == "POST":
        messages = MentorMessage.objects.filter(session_user_id=session_user_id, mentor_type=mentor_type, is_read=False).exclude(sender=request.user)
        messages.update(is_read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=405)
