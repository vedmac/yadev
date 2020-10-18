from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    """Group model"""
    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('Ярлык', unique=True, null=True)
    description = models.TextField('Описание', null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Post(models.Model):
    """Post model"""
    text = models.TextField('Текст')
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='author_posts',
                               verbose_name='Автор')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              blank=True, null=True, related_name='posts',
                              verbose_name='Группа')
    image = models.ImageField(upload_to='posts/', blank=True,
                              null=True, verbose_name='Картинка')

    def __str__(self):
        return self.text

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField('Комментарий', max_length=200)
    created = models.DateTimeField("Дата комментария", auto_now_add=True,
                                   db_index=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Пользователь')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Автор')

    class Meta:
        unique_together = ("user", "author")
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
