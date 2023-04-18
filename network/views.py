from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

from .models import User, Post, Follow, Like


def remove_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.get(pk=user, post=post)
    like.delete()
    return JsonResponse({"message": "Like removed!"})


def add_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.get(pk=user, post=post)
    like.save()
    return JsonResponse({"message": "Like added!"})


def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()
    
    paginator = Paginator(allPosts, 10)
    pageNumber = request.GET.get('page')
    postOnPage= paginator.get_page(pageNumber)

    allLikes = Like.objects.all
    whoLiked = []
    try:
        for like in allLikes:
            if like.poster.id == request.user.id:
                whoLiked.append(like.post.id)
    except:
        whoLiked = []

    return render(request, "network/index.html", {
        "allPosts": allPosts,
        "postOnPage": postOnPage,
        ":whoLiked": whoLiked
    })



def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(poster=user).order_by("id").reverse()

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    try:
        checkFollow = followers.filter(user=User.objects.get(pk=request.user.id))
        if len(checkFollow) != 0:
            isFollowing = True
        else:
            isFollowing = False
    except:
        isFollowing = False
    
    
    paginator = Paginator(allPosts, 10)
    pageNumber = request.GET.get('page')
    postOnPage= paginator.get_page(pageNumber)

    return render(request, "network/profile.html", {
        "allPosts": allPosts,
        "postOnPage": postOnPage,
        "username": user.username,
        "following": following,
        "followers": followers,
        "isFollowing": isFollowing,
        "user_profile": user
    })



def follow(request):
    userFollow = request.POST['userfollow']
    currentUser = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userFollow)
    f = Follow(user=currentUser, user_follower=userfollowData)
    f.save()
    user_id = userfollowData.id 
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))



def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    followingPeople = Follow.objects.filter(user=currentUser)
    allPosts = Post.objects.all().order_by('id').reverse()

    followingPosts = []

    for post in allPosts:
        for person in followingPeople:
            if person.user_follower == post.poster:
                followingPosts.append(post)

    paginator = Paginator(followingPosts, 10)
    pageNumber = request.GET.get('page')
    postOnPage= paginator.get_page(pageNumber)

    return render(request, "network/following.html", {
        "postOnPage": postOnPage
    })


def edit(request, post_id):
    if request.method == "POST":
        # Parse the request body as JSON
        data = json.loads(request.body)
        
        # Get the Post object with the given post_id
        edit_post = Post.objects.get(pk=post_id)
        
        # Update the content field of the Post object
        edit_post.content = data["content"]
        
        # Save the changes
        edit_post.save()
        
        # Return a JSON response indicating the changes were successful
        return JsonResponse({"message": "change successful", "data": data["content"]})

def unfollow(request):
    userFollow = request.POST['userfollow']
    currentUser = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userFollow)
    f = Follow.objects.get(user=currentUser, user_follower=userfollowData)
    f.delete()
    user_id = userfollowData.id 
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def newPost(request):
    if request.method == "POST":
        content = request.POST['content']
        poster = User.objects.get(pk=request.user.id)
        post = Post(content=content, poster=poster)
        post.save()
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
