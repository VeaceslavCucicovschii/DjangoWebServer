from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    body = models.CharField(max_length=200, default="")

class Reaction(models.Model):
    type = models.CharField(max_length=30)

class CustomUser(User):
    avatar = models.CharField(max_length=150, default="")
    friends = models.ManyToManyField('self')
    session_data_backup = models.TextField(default='')

class Post(models.Model):
    title = models.CharField(max_length=100)
    body = models.CharField(max_length=200, default="")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=None)

class Comment(models.Model):
    body = models.CharField(max_length=200, default="")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=None)