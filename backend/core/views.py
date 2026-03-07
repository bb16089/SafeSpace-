from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .forms import SignupForm, AdminInsightForm, AdminNotificationForm
from .models import Post, Reply, Reaction, Insight, Notification, ANON_NAMES
import json, random

# ----------------- ADMIN PANEL -----------------

@staff_member_required(login_url='login')
def admin_dashboard(request):
    insights_count = Insight.objects.count()
    notifications_count = Notification.objects.count()
    posts_count = Post.objects.count()
    return render(request, 'admin_dashboard.html', {
        'insights_count': insights_count,
        'notifications_count': notifications_count,
        'posts_count': posts_count
    })

@staff_member_required(login_url='login')
def manage_insights(request):
    insights = Insight.objects.all().order_by('-created_at')
    if request.method == 'POST':
        form = AdminInsightForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_insights')
    else:
        form = AdminInsightForm()
    return render(request, 'admin_manage_insights.html', {'insights': insights, 'form': form})

@staff_member_required(login_url='login')
def delete_insight(request, insight_id):
    insight = get_object_or_404(Insight, id=insight_id)
    insight.delete()
    return redirect('manage_insights')

@staff_member_required(login_url='login')
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

@staff_member_required(login_url='login')
def delete_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    notif.delete()
    return redirect('manage_notifications')

@staff_member_required(login_url='login')
def manage_posts(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'admin_manage_posts.html', {'posts': posts})

@staff_member_required(login_url='login')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect('manage_posts')

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

@login_required
def dashboard(request):
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

