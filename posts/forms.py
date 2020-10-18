from django import forms
from django.forms import ModelForm
from .models import Comment, Post


class PostForm(ModelForm):
    """Form for creating new post"""
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        help_texts = {
            'group': 'Можно не выбирать группу',
            'text': 'Hапишите свой текст здесь',
            'image': 'Добавьте картинку'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': forms.Textarea, }
