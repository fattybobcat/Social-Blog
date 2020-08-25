from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    """
    Description of the Post model.
    Parameters
    -------
    text: TextField()
        The text of the post
    pub_date: DateTimeField()
        Date of publication
    author:  ForeignKey, link -> User
        Author of the post
    group:   ForeignKey, link ->Group
        Link to the community(if available)
    """
    text = models.TextField()
    pub_date = models.DateTimeField("date published",
                                    auto_now_add=True,
                                    db_index=True,
                                    )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="posts"
                               )
    group = models.ForeignKey("Group",
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name="posts"
                              )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ('-pub_date',)


class Group(models.Model):
    """
    Description of the community model.
    Parameters
    -------
    title: CharField()
        The name. Max length 200
    slug: SlugField()
        The unique address of the group, part of the URL
    description:  TextField
        Text that appears on the community page.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    """
        Description of the comment model.
        Parameters
        -------
        post: CharField()
            The name. Max length 200
        author: ForeignKey, link -> User
            Author of the post
        text:  TextField
            Text that appears on the community page.
        created: DateTimeField()
            Date of created
    """
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             blank=True,
                             null=False,
                             related_name="comments"
                             )
    author = models.ForeignKey(User,
                              on_delete=models.CASCADE,
                              related_name="comments",
                               )
    text = models.TextField()
    created = models.DateTimeField("created",
                                   auto_now_add=True,
                                   )


class Follow(models.Model):
    """
        Description of the follow model.
        Parameters
        -------
        user: CharField()
            The name. Max length 200
        author: ForeignKey, link -> User
            Author of the post
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="follower"
                             )
    author = models.ForeignKey(User,
                              on_delete=models.CASCADE,
                              related_name="following",
                               )
