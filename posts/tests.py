from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Follow, Group, Post, User


class PostTest(TestCase):

    def setUp(self):
        """Create client and User"""
        self.client = Client()
        self.client_anon = Client()
        self.user = User.objects.create(
            username="Bender", password="12345", email="bender@robot.com"
            )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            slug="Test_slug",
            title="Test_group",
            description="Test_description")
        self.post = Post.objects.create(text="Who am I?",
                                        author=self.user,
                                        group=self.group)

    def text_search(self, text=None, post_id=None):
        if text is None:
            text = self.post.text
        if post_id is None:
            post_id = self.post.id
        for url in (
                reverse("index"),
                reverse("profile",
                        kwargs={"username": self.user.username}),
                reverse("post",
                        kwargs={"username": self.user.username,
                                "post_id": post_id, })
        ):
            response = self.client.get(url)
        self.assertContains(response, text)

    def test_profile_create(self):
        """Check profile"""
        print("Test 1. Check profile")
        response_code = self.client.get(reverse("profile",
                                                kwargs={"username": "Bender"})
                                        )
        self.assertEqual(response_code.status_code, 200)

    def test_create_post(self):
        """Create post and check in DB & url"""
        print("Test 2. Create post. Check in DB and url")
        text_new = "kiss me on my shiny!(с) Bender"
        self.client.post(reverse("new_post"),
                         {"text": text_new})
        post_count = Post.objects.filter(text=text_new).count()
        self.assertEqual(post_count, 1)
        post = Post.objects.get(text=text_new)
        self.text_search(text_new, post.id)

    def test_anonymous_user(self):
        """"Check anonymous user - post don't create, redirect"""
        print("Test 3. Anonymous user can't create post")
        text_anon = 'new post from anonymous'
        response = self.client_anon.post(reverse('new_post'),
                                         {'text': 'new post from anonymous'})
        posts_count = Post.objects.filter(text=text_anon).count()
        self.assertEqual(posts_count, 0)
        self.assertRedirects(response, "/auth/login/?next=/new", 302)

    def test_post_edit(self):
        """Edit and check edited post on url and in DB"""
        print("Test 4. Edit post and check edited post in url & DB")
        text_edit = 'Whooo?'
        response = self.client.post(
            reverse("post_edit",
                    kwargs={"username": self.post.author,
                            "post_id": self.post.id},),
            {'text': text_edit}, follow=True
        )
        posts = Post.objects.filter(text=text_edit)
        self.assertEqual(posts[0].text, text_edit)
        self.text_search(text_edit)
        self.assertEqual(response.status_code, 200)

    def test_404(self):
        print("Test 5. 404")
        response = self.client.post("/4ss4/")
        self.assertEqual(response.status_code, 404)

    def test_500(self):
        print("Test 6. 500")
        response = self.client.post("/500/")
        self.assertEqual(response.status_code, 500)

    def test_post_with_image(self):
        print("Test 7. Image in post")
        cache.clear()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            name='some.gif',
            content=small_gif,
            content_type='image/gif',
        )
        post = Post.objects.create(
            author=self.user,
            text="text",
            image=img,
        )
        urls = [
            reverse("profile",
                    kwargs={"username": self.user.username}),
            reverse("index"),
            reverse("post", args=[self.user.username, post.id])
        ]
        for url in urls:
            with self.subTest(url=url):
                respose = self.client.post(url)
                self.assertContains(respose, "<img")

    def test_cache(self):
        print("Test 9. test cache")
        response_before_post = self.client.get(reverse('index'))
        post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='test cache post')
        response_after_post = self.client.get(reverse('index'))
        self.assertEqual(response_before_post.content, response_after_post.content)
        self.assertNotContains(response_before_post, post.text)
        cache.clear()
        response_after_cache = self.client.get(reverse('index'))
        self.assertNotEqual(response_after_post.content, response_after_cache.content)
        self.assertContains(response_after_cache, post.text)

    def test_load_no_mage(self):
        print("Test 8. Not image load in post")
        not_img = SimpleUploadedFile(
            name='some.txt',
            content=b'abc',
            content_type='text/plain',
        )
        url = reverse("new_post")
        response = self.client.post(url,
                                    {"text": "test_text",
                                     "image": not_img}
                                    )
        self.assertFormError(
            response,
            "form",
            "image",
            errors='Загрузите правильное изображение. '
                   'Файл, который вы загрузили, поврежден '
                   'или не является изображением.',
        )


class FollowTest(TestCase):
    """"Tests group2. 1. Follow and unfollow"""
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="first_user",
            email="first_user@testmail.ru",
            password="12345",
        )
        self.post1 = Post.objects.create(
            text="test message1", author=self.user1,
        )
        self.client.force_login(self.user1)
        self.user2 = User.objects.create_user(
            username="second_user",
            email="second_user@testmail.ru",
            password="12345",
        )
        self.post2 = Post.objects.create(
            text="test message2", author=self.user2,
        )
        self.client3 = Client()
        self.user3 = User.objects.create_user(
            username="third_user",
            email="third_user@testmail.ru",
            password="12345",
        )
        self.client3.force_login(self.user3)
        self.client_anon = Client()

    def test_following_authuser(self):
        print("Test 2-1. Follow by auth user")
        user2_profile = self.client.get(
            reverse("profile",
                    kwargs={"username": self.user2.username})
        )
        self.assertContains(user2_profile, "Подписаться")
        self.client.get(reverse("profile_follow",
                                kwargs={"username": self.user2.username})
                        )
        user2_profile = self.client.get(
            reverse("profile",
                    kwargs={"username": self.user2.username})
        )
        self.assertContains(user2_profile, "Отписаться")
        self.assertEqual(len(Follow.objects.all()), 1)

    def test_unfollowing_authuser(self):
        print("Test 2-2. Unfollow by auth user")
        self.client.get(reverse("profile_follow",
                                kwargs={"username": self.user2.username})
                        )
        self.assertEqual(len(Follow.objects.all()), 1)
        user2_profile = self.client.get(
            reverse("profile",
                    kwargs={"username": self.user2.username})
        )
        self.assertContains(user2_profile, "Отписаться")
        self.client.get(reverse("profile_unfollow",
                                kwargs={"username": self.user2.username})
                        )
        user2_profile = self.client.get(
            reverse("profile",
                    kwargs={"username": self.user2.username})
        )
        self.assertContains(user2_profile, "Подписаться")
        self.assertEqual(len(Follow.objects.all()), 0)

    def test_following_post_in_lent(self):
        print("Test 2-3. New post in follow-lent ",
              "for followers and not post for unfollowers")
        response_code = self.client.get(
            reverse("profile_follow",
                    kwargs={"username": self.user2.username})
        )
        self.assertEqual(len(Follow.objects.all()), 1)
        text_post_user_2 = "new post for followers"
        response_code = self.client.get(reverse("follow_index"))
        self.assertNotContains(response_code, text_post_user_2)
        self.post3 = Post.objects.create(
            text=text_post_user_2, author=self.user2,
        )
        response_code = self.client.get(reverse("follow_index"))
        self.assertContains(response_code, text_post_user_2)
        response_code = self.client3.get(reverse("follow_index"))
        self.assertNotContains(response_code, text_post_user_2)

    def test_only_auth_user_can_commit_post(self):
        print("Test 2-4. Add new commit by auth user")
        post_1 = Post.objects.get(pk=1)
        text_comment = "Commentary1"
        text_comment2 = "Commentary2"
        self.client.post(reverse("add_comment",
                                 kwargs={"username": self.user1.username,
                                         "post_id": post_1.id,
                                         }
                                 ),
                         {"text": text_comment}
                         )
        response_code = self.client.get(
            reverse("post",
                    kwargs={"username": self.user1.username,
                            "post_id": post_1.id},
                    )
        )
        self.assertContains(response_code, text_comment)
        self.client_anon.post(reverse("add_comment",
                                      kwargs={"username": self.user1.username,
                                              "post_id": post_1.id,
                                              }), {"text": text_comment2})
        response_code = self.client.get(
            reverse("post",
                    kwargs={"username": self.user1.username,
                            "post_id": post_1.id},
                    )
        )
        self.assertNotContains(response_code, text_comment2)
