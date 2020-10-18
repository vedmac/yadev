import tempfile
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from posts.models import Comment, Follow, Group, Post, User
from PIL import Image


class PostsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='Conor')

    def test_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['profile'], User)
        self.assertEqual(
            response.context['profile'].username, self.user.username)

    def test_new_post_user(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(text='Новый пост', author=self.user)
        self.assertEqual(Post.objects.count(), 1)

    def test_new_post_guest(self):
        response = self.client.post(
            reverse('new_post'),
            data={'group': '', 'text': 'Новый пост'},
            follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')
        self.assertEqual(Post.objects.all().count(), 0)

    def url_check(self, post):
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post', kwargs={
                    'username': self.user.username, 'post_id': self.post.id})
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, self.post.text)

    def test_new_post_user_pages(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(text='Новый пост', author=self.user)
        cache.clear()
        self.url_check(self.post)

    def test_edit_post_user(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(text='Новый пост', author=self.user)
        response = self.client.get(
            reverse('post_edit', kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)
        self.client.post(
            reverse('post_edit', kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id}),
            {'text': 'Измененный текст'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, 'Измененный текст')
        self.url_check(self.post)

    def test_404(self):
        response = self.client.get('request/wrong/url/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'misc/404.html')
# ------------------------New tests---------------


class TestComment(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(username='member')
        self.guest = User.objects.create_user(username='guest')
        self.auth_member = Client()
        self.no_auth_guest = Client()
        self.auth_member.force_login(self.member)

    def test_post_comment_user(self):
        post = Post.objects.create(
            text='Test comment by auth user', author=self.member)
        response = self.auth_member.post(
            reverse(
                'add_comment', kwargs={'username': self.member,
                                       'post_id': post.id, }),
            data={'text': 'test comment'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Comment.objects.filter(post=post, text='test comment').exists(),
            'Комментарий не создался в базе',
        )
        response = self.auth_member.get(
            reverse(
                'post', kwargs={'username': self.member.username,
                                'post_id': post.id}),)
        self.assertContains(response, 'test comment', status_code=200)

    def test_post_comment_guest(self):
        post = Post.objects.create(
            text='Test comment by non auth user', author=self.member
        )
        self.no_auth_guest.logout()
        response = self.no_auth_guest.post(
            reverse(
                'add_comment',
                kwargs={'username': self.auth_member, 'post_id': post.id, },
            ),
            data={'text': "You can't comment!"},
            follow=True,
        )
        response = self.auth_member.get(
            reverse(
                'post', kwargs={'username': self.member.username,
                                'post_id': post.id}), )
        self.assertNotEqual(response, "You can't comment!")


class TestFollowings(TestCase):
    def setUp(self):
        self.follower = User.objects.create_user(username='follower')
        self.bloger = User.objects.create_user(username='bloger')
        self.not_follow = User.objects.create_user(username='guest')
        self.auth_follower = Client()
        self.auth_bloger = Client()
        self.auth_not_follow = Client()
        self.auth_follower.force_login(self.follower)
        self.auth_not_follow.force_login(self.not_follow)
        self.post = Post.objects.create(
            text='This post for test subscribes', author=self.bloger
        )
        self.urls_list = [
            reverse('profile', kwargs={'username': self.follower.username}),
            reverse(
                'post',
                kwargs={'username': self.bloger.username,
                        'post_id': self.post.id},), ]

    def check_post_on_page(self, client, url, post_text, user, group):
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        if 'paginator' in response.context:
            check_post = response.context['page'][0]
        else:
            check_post = response.context['post']

        self.assertEqual(check_post.text, post_text)
        self.assertEqual(check_post.group, group)
        self.assertEqual(check_post.author, user)

    def test_follow(self):
        for url in self.urls_list:
            with self.subTest(url=url):
                follow = Follow.objects.filter(user=self.follower,
                                               author=self.bloger)
                if follow:
                    follow.delete()
                response = self.auth_follower.post(
                    reverse('profile_follow',
                            kwargs={'username': self.bloger.username}
                            ),
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        for url in self.urls_list:
            with self.subTest(url=url):
                Follow.objects.get_or_create(user=self.follower,
                                             author=self.bloger)
                response = self.auth_follower.post(
                    reverse('profile_unfollow',
                            kwargs={'username': self.bloger.username}
                            ),
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Follow.objects.count(), 0)

    def test_post_on_subscribes_page(self):
        post_text = 'Test post'
        post = Post.objects.create(text=post_text, author=self.bloger)
        Follow.objects.create(user=self.follower, author=self.bloger)
        self.assertEqual(Follow.objects.count(), 1)
        url = reverse('follow_index')
        self.check_post_on_page(self.auth_follower, url,
                                post_text, self.bloger, None)
        response = self.auth_not_follow.get(url)
        self.assertNotIn(
            post,
            response.context['page'],
            'Пользователь не подписан на автора, но видит его посты',
        )


class TestCache(TestCase):
    def setUp(self):
        self.first_client = Client()
        self.second_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.first_client.force_login(self.user)

    def test_cache(self):
        self.second_client.get(reverse('index'))
        self.first_client.post(reverse('new_post'), {'text': 'Test text'})
        response = self.second_client.get(reverse('index'))
        self.assertNotContains(response, 'Test text')


class TestImg(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='TestImg')
        self.client.force_login(self.user)
        self.group = Group.objects.create(title='TestGroup',
                                          slug='test',
                                          description='TestImgGroup',
                                          )
        self.post = Post.objects.create(text='Test', group=self.group,
                                        author=self.user)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img:
            image = Image.new('RGB', (200, 200), 'black')
            image.save(img, 'PNG')
        self.image = open(img.name, mode='rb')

        with tempfile.NamedTemporaryFile(suffix='.doc',
                                         delete=False) as not_img:
            not_img.write(b'test')
        self.not_image = open(not_img.name, 'rb')

    def test_pages_with_img(self):
        with self.image as img:
            self.client.post(reverse('post_edit',
                                     kwargs={'username': self.user,
                                             'post_id': self.post.id}),
                             {'group': self.group.id,
                              'text': 'post with image',
                              'image': img}, redirect=True)

        tag = '<img '
        cache.clear()
        response_profile = self.client.get(reverse(
            'profile', kwargs={'username': self.user.username}))
        response_index = self.client.get(reverse('index'))
        response_group = self.client.get(reverse(
            'group', kwargs={'slug': self.group.slug}))

        self.assertContains(response_index, tag)
        self.assertContains(response_profile, tag)
        self.assertContains(response_group, tag)

    def test_wrong_format(self):
        with self.not_image as img:
            wrong_img = self.client.post(reverse('post_edit',
                                                 kwargs={'username': self.user,
                                                         'post_id':
                                                             self.post.id}),
                                         {'group': self.group.id,
                                          'text': 'post with image',
                                          'image': img}, redirect=True)

        error = ('Загрузите правильное изображение. Файл, который вы '
                 'загрузили, поврежден или не является изображением.')
        self.assertFormError(wrong_img, 'form', 'image', error)
