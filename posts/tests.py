from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from .models import Group, Post, User

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
        response = self.client.post(reverse("new_post"), {"text": text_new})
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

    def test_load_no_mage(self):
        print("Test 8. Test 8. Not image load in post")
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

    def test_cached_post_index(self):
        print("Test 9. Cache post on index")
        self.client.get("index")
        post_c = Post.objects.all().count()
        print(post_c)
        self.client.post(reverse("new_post"), {"text": "testcached2"})
        post_c = Post.objects.all().count()
        print(post_c)
        self.client.post(reverse("new_post"), {"text": "testcached3"})
        post_c = Post.objects.all().count()
        print(post_c)
        response = self.client.get(reverse("index"))

        self.assertEqual(response.context['paginator'].count, 2)

        self.assertNotEqual(cache.get('index_page', 'nothing'), 'nothing')