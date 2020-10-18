from django.contrib import admin
from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    """Post fields that are displayed in the admin panel"""
    list_display = ("pk", "text", "pub_date", "author")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    """Group fields that are displayed in the admin panel"""
    list_display = ("title", "slug", "description")
    search_fields = ("text",)
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'text',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    search_fields = ('author',)
    list_filter = ('user', 'author',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
