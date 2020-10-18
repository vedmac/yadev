from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .models import Comment, Follow, Group, Post, User
from .forms import CommentForm, PostForm


@cache_page(20, key_prefix='index_page')
def index(request):
    """View function for Index page"""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    """View function for community page"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html',
                  {'group': group,
                   'page': page,
                   'paginator': paginator, }
                  )


@login_required
def new_post(request):
    """View function for creating new post page"""
    if request.method == "POST":
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
    else:
        form = PostForm()
    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    """Adds a profile page with posts"""
    author = get_object_or_404(User, username=username)
    post_list = author.author_posts.all()
    count_posts = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = (Follow.objects.filter(user=request.user,
                                       author=author).exists()
                 if request.user.is_authenticated else False)
    return render(request, 'profile.html', {
        'page': page,
        'paginator': paginator,
        'count_posts': count_posts,
        'profile': author,
        'following': following})


def post_view(request, username, post_id):
    """Creates a Page for viewing a separate post"""
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.author_posts, id=post_id)
    selected_post = get_object_or_404(Post, pk=post_id,
                                      author__username=username)
    count_posts = author.author_posts.count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    return render(request, 'post_view.html', {
        'profile': author,
        'selected_post': selected_post,
        'count_posts': count_posts,
        'form': form,
        'post': post,
        'comments': comments})


@login_required
def post_edit(request, username, post_id):
    """Creating a page for editing an existing post"""
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path},
                  status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post_id = post_id
        form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    authors = user.follower.all().values('author')
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page,
                                           'paginator': paginator})


@login_required()
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follows = user.follower.filter(author=author)
    follows.delete()
    return redirect('index')
