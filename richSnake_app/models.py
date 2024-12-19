import random
import string

from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class Task(models.Model):
    class Types(models.TextChoices):
        COIN = "coin", "Coin"
        DOLLAR = "dollar", "Dollar"

    source = models.CharField(max_length=255)
    source_image = models.ImageField(upload_to='task_images/', null=True)
    title = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255, null=True)
    description = models.TextField()
    description_ru = models.TextField(null=True)
    link = models.URLField()
    score = models.IntegerField()
    type = models.CharField(max_length=20, choices=Types.choices, default="coin")

    class Meta:
        verbose_name_plural = 'Task'

    def __str__(self):
        return self.title


class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', null=True)
    score = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)
    record = models.IntegerField(default=0)
    wallet_address = models.CharField(max_length=100, null=True, blank=True)
    completed_tasks = models.ManyToManyField(Task, through='UserTask', related_name='completed_by')

    class Meta:
        verbose_name_plural = 'User'

    def __str__(self):
        return self.username

    def generate_unique_username(self):
        while True:
            random_string = ''.join(random.choices(string.ascii_lowercase, k=7))
            random_number = ''.join(random.choices(string.digits, k=3))
            username = f"{random_string}{random_number}"

            # Check if this username already exists
            if not User.objects.filter(username=username).exists():
                return username

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.generate_unique_username()
        super().save(*args, **kwargs)


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


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expire_time = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Subscription"


class WithdrawRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdraw_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wallet_address = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'WithdrawRequests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Withdraw Request for {self.user.username} - {self.amount} ({self.status})"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.TELEGRAM)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['payment_method', 'status'])
        ]

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.payment_method}, {self.status})"

