from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    google_id = models.CharField(max_length=100, unique=True)
    solana_address = models.CharField(max_length=44, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Token(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    total_supply = models.DecimalField(max_digits=30, decimal_places=9)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Transaction(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='transactions')
    from_address = models.CharField(max_length=44)
    to_address = models.CharField(max_length=44)
    amount = models.DecimalField(max_digits=30, decimal_places=9)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'token']
