from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Task(models.Model):
    source = models.CharField(max_length=255)
    source_image = models.ImageField(upload_to='task_images/', null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    link = models.URLField()
    score = models.IntegerField()

    class Meta:
        verbose_name_plural = 'Task'

    def __str__(self):
        return self.title

class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', null=True)
    score = models.IntegerField(default=0)
    completed_tasks = models.ManyToManyField(Task, through='UserTask', related_name='completed_by')

    class Meta:
        verbose_name_plural = 'User'

    def __str__(self):
        return self.username


class Prize(models.Model):
    image = models.ImageField(upload_to='prizes/', null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = 'Prize'


    def __str__(self):
        return self.title


class UserTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_users')

    class Meta:
        verbose_name_plural = 'UserTask'
        unique_together = ('user', 'task')


    def __str__(self):
        return self.user.username +' ' + self.task.title
    
import random
import string

class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral')
    referral_code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name_plural = 'Referral'


    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

class ReferredUser(models.Model):
    referred_by = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='referred_users')
    referred_user = models.OneToOneField(User, on_delete=models.CASCADE)
    earned_score = models.IntegerField(default=10)

    class Meta:
        verbose_name_plural = 'ReferredUsers'


    def __str__(self):
        return f"{self.referred_user.username} reffered by {self.referred_by.user.username}"