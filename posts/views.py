from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.select_related("author", "group").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request,
                  "index.html",
                  {"page": page,
                   "paginator": paginator,
                   "post": post_list},
                  )


def group_posts(request, slug):
    """Returns posts that belong to a specific community"""
    group = get_object_or_404(Group, slug=slug)
    posts_group = group.posts.all()
    paginator = Paginator(posts_group, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request,
                  "group.html",
                  {"page": page,
                   "group": group,
                   "paginator": paginator
                   }
                  )


@login_required
def new_post(request):
    """Create new posts"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            new_article = form.save(commit=False)
            new_article.author = request.user
            new_article.save()
            return redirect("index")

    return render(request,
                  "new.html",
                  {"form": form}
                  )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_count = author.posts.count()
    author_posts = author.posts.all()
    following_count = author.following.count()
    follower_count = author.follower.count()
    paginator = Paginator(author_posts, 3)
    page = paginator.get_page(request.GET.get("page"))
    following = author.following.all()
    return render(request, "profile.html", {
        "page": page,
        "paginator": paginator,
        "posts_count": posts_count,
        "author": author,
        "following_count": following_count,
        "follower_count": follower_count,
        "following": following,
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    posts_count = author.posts.count()
    following_count = author.following.count()
    follower_count = author.follower.count()
    items = post.comments.all()
    form = CommentForm()
    following = author.following.all()
    return render(request,
                  "post.html",
                  {"post": post,
                   "author": author,
                   "posts_count": posts_count,
                   "items": items,
                   "form": form,
                   "following_count": following_count,
                   "follower_count": follower_count,
                   "following": following,
                   })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return post_view(request, username, post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    form_content = {"form": form, "post": post, "post_edit": True}
    if form.is_valid():
        post.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request,
                  "new.html",
                  form_content)


def page_not_found(request, exception=None):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    items = post.comments.all()
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("post", username=username, post_id=post_id)
    context = {
        "post_author": post.author,
        "post": post,
        "form": CommentForm(),
        "items": items,
    }
    return render(request, "comments.html", context)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request,
                  "follow.html",
                  {"page": page,
                   "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect("profile", username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("profile", username)
