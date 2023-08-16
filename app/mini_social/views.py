# views module
from django.http import HttpResponse, HttpResponseForbidden
from django.template import loader
from django.shortcuts import redirect

from random import randint
from .models import Post, Comment
import json

from .models import CustomUser
from django.contrib.auth import authenticate, login, logout, get_user

from django.contrib import messages
from django.contrib.sessions.models import Session

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# AKA DATABASE

users = [
    {"username": "Johny", "created":   "2000-01-01"},
    {"username": "marry", "created":   "2000-01-02"},
    {"username": "pete", "created":    "2000-01-03"},
    {"username": "vasilyi", "created": "2000-01-04"},
    {"username": "masha", "created":   "2000-01-05"},
    {"username": "lily", "created":    "2000-01-06"},
]

posts = [
    {"title": "First title", "created":  "2001-01-01"},
    {"title": "Second title", "created": "2001-01-02"},
    {"title": "Third title", "created":  "2001-01-03"},
    {"title": "Forth title", "created":  "2001-01-04"},
    {"title": "Fifth title", "created":  "2001-01-05"},
]

def homePage(request):
    def takeDate(elem):
        return elem["created"]

    template = loader.get_template("home.html")

    users.sort(key=takeDate, reverse=True)
    posts.sort(key=takeDate, reverse=True)

    return HttpResponse(template.render({
        "last_users": users[:5],
        "last_posts": posts[:3],
        "user": request.user,
    }, request))

# USER VIEWS

def registerUser(request):
    if request.method == "GET":
        template = loader.get_template("user/register.html")
        return HttpResponse(template.render({}, request))
    
    elif request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            messages.error(request, "password didn't match")
            return redirect("/user/register")
        
        if len(password) > 15:
            messages.error(request, "password to long, ['max password length = 15']")
            return redirect("/user/register")
        
        try: 
            validate_email(email)
        except ValidationError as e:
            messages.error(request, f"invalid email, details: {e}")
            return redirect("/user/register")

        CustomUser.objects.create_user(username, email, password)

        user = authenticate(username=username, password=password)
        login(request, user)

        messages.success(request, 'Account has been created and login successful!')
        return redirect("/")

def loginUser(request):
    if request.method == "GET":
        template = loader.get_template("user/login.html")
        return HttpResponse(template.render({}, request))
    
    elif request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, 'Wrong creadentials!')
            return redirect("/user/login")
        
        login(request, user)
        visitingUser = CustomUser.objects.get(pk=user.id)
        
        session_data_backup = visitingUser.session_data_backup
        session_data = json.loads(session_data_backup if session_data_backup else '{}')

        request.session.update(session_data)

        messages.success(request, 'Login successful!')
        return redirect("/")

def logoutUser(request):
    visitingUser = get_user(request)
    visitingUser = CustomUser.objects.get(pk=visitingUser.id)
    
    session = Session.objects.get(pk=request.session.session_key)
    session_data = session.get_decoded()

    session_data_json = json.dumps(session_data)

    visitingUser.session_data_backup = session_data_json

    visitingUser.save()
    logout(request)

    return redirect("/")
    
def toggleUserNotifications(request):
    visitingUser = get_user(request)
    toggle = request.GET.get('toggle', None)
    
    if not toggle:
        request.session['show_notifications'] = False
    else:
        request.session['show_notifications'] = True

    return redirect(f"/user/profile/{visitingUser.id}")

def userProfile(request, id):
    if request.method == "GET":
        profileUser = CustomUser.objects.get(pk=id)
        visitingUser = get_user(request)
        visitingUser = CustomUser.objects.get(pk=visitingUser.id)
        template = loader.get_template("user/profile.html")

        userFriends = profileUser.friends.all()
        profileUserIsNotVisitingUserFriend = visitingUser.friends.all().contains(profileUser)

        profileUserPosts = Post.objects.filter(author=profileUser.pk)
        
        show_notifications = request.session.get('show_notifications', None)

        return HttpResponse(template.render({
            'profileUser': profileUser, 
            'visitingUser': visitingUser,
            'userFriends': userFriends,
            'profileUserIsNotVisitingUserFriend': profileUserIsNotVisitingUserFriend,
            'show_notifications': show_notifications,
            'profileUserPosts': profileUserPosts,
        }, request))
    
def editUserProfile(request, id):
    if request.method == "GET":

        profileUser = CustomUser.objects.get(pk=id)
        visitingUser = get_user(request)

        if profileUser.id == visitingUser.id:
            template = loader.get_template("user/edit-profile.html")
            return HttpResponse(template.render({
                'profileUser': profileUser, 
                'visitingUser': visitingUser
            }, request))
        else:
            return HttpResponseForbidden('Access Denied!')
        
    elif request.method == 'POST':

        profileUser = CustomUser.objects.get(pk=id)
        visitingUser = get_user(request)

        if profileUser.id == visitingUser.id:
            avatar = request.FILES['avatar']
            avatar_file = open(f"app/public/uploads/{avatar}", "wb+")
        
            for chunk in avatar.chunks():
                avatar_file.write(chunk)
        
            avatar_file.close()

            profileUser.avatar = f"uploads/{avatar}"
            profileUser.save()

            return redirect(f'/user/profile/{profileUser.id}')
        else:
            return HttpResponseForbidden('Access Denied!')
        
def addUserFriend(request, id):
    if request.method == "GET":
        profileUser = CustomUser.objects.get(pk=id)
        visitingUser = get_user(request)
        visitingUser = CustomUser.objects.get(pk=visitingUser.id)

        visitingUser.friends.add(profileUser)
        visitingUser.save()

        return redirect(f"/user/profile/{profileUser.id}")
    
def removeUserFriend(request, id):
    if request.method == "GET":
        profileUser = CustomUser.objects.get(pk=id)
        visitingUser = get_user(request)
        visitingUser = CustomUser.objects.get(pk=visitingUser.id)

        visitingUser.friends.remove(profileUser)

        return redirect(f"/user/profile/{visitingUser.id}")

# POST VIEWS

def addPost(request):
    visitingUser = get_user(request)
    visitingUser = CustomUser.objects.get(pk=visitingUser.id)
    
    if request.method == "GET":
        template = loader.get_template("post/create.html")

        return HttpResponse(template.render({
            "visitingUser": visitingUser
        }, request))
    
    elif request.method == "POST":
        title = request.POST["title"]
        body = request.POST["body"]

        post = Post(title=title, body=body, author=visitingUser)
        post.save()

        return redirect(f'/user/profile/{visitingUser.id}')

def updatePost(request, id):
    visitingUser = get_user(request)
    visitingUser = CustomUser.objects.get(pk=visitingUser.id)
    
    if request.method == "GET":
        post = Post.objects.get(pk=id)

        template = loader.get_template("post/update.html")
        return HttpResponse(template.render({
            "post": post,
            "visitingUser": visitingUser,
        }, request))

    elif request.method == "POST":
        new_title = request.POST['title']
        new_body = request.POST['body']

        post = Post.objects.get(pk=id)

        post.title = new_title
        post.body = new_body

        post.save()

        return redirect(f"/user/profile/{visitingUser.id}")

def deletePost(request, id):
    if request.method == "GET":
        post = Post.objects.get(pk=id)
        post.delete()

        return redirect(f"/user/profile/{request.user.id}")

def postPage(request, id):
    if request.method == "GET":
        visitingUser = get_user(request)
        visitingUser = CustomUser.objects.get(pk=visitingUser.id)
        
        post = Post.objects.get(pk=id)
        comments = Comment.objects.filter(post=id)

        template = loader.get_template("post/page.html")

        return HttpResponse(template.render({
            'visitingUser': visitingUser,
            'post': post,
            'comments': comments,
        }, request))

# COMMENT VIEWS

def addComment(request, id):
    visitingUser = get_user(request)
    visitingUser = CustomUser.objects.get(pk=visitingUser.id)
    
    post = Post.objects.get(pk=id)

    if request.method == "GET":
        template = loader.get_template("comment/create.html")

        return HttpResponse(template.render({
            "visitingUser": visitingUser,
            "post": post,
        }, request))
    
    elif request.method == "POST":
        body = request.POST["body"]

        comment = Comment(body=body, post=post, author=visitingUser)
        comment.save()

        return redirect(f'/post/page/{id}')