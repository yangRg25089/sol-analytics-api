from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        user_type = extra_fields.pop("user_type", "google")
        if user_type == "google" and not extra_fields.get("google_id"):
            raise ValueError("Google users must have a google_id")

        user = self.model(email=email, user_type=user_type, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields["user_type"] = "admin"

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ("admin", "Admin User"),
        ("google", "Google User"),
    ]

    id = models.AutoField(primary_key=True)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="google"
    )
    google_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True, db_index=True
    )
    email = models.EmailField(unique=True, null=False, blank=False, db_index=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    solana_address = models.CharField(
        max_length=44, null=True, blank=True, db_index=True
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    role = models.CharField(max_length=50, default="user")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user_type="google", google_id__isnull=False)
                | models.Q(user_type="admin", google_id__isnull=True),
                name="valid_user_type_constraint",
            )
        ]

    def clean(self):
        super().clean()
        if self.user_type == "google" and not self.google_id:
            raise ValidationError("Google users must have a google_id")
        if self.user_type == "admin" and self.google_id:
            raise ValidationError("Admin users should not have a google_id")

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.email or self.google_id or str(self.id)


class Token(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, db_index=True)
    total_supply = models.BigIntegerField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_tokens",
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Transaction(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.ForeignKey(
        Token, on_delete=models.CASCADE, related_name="transactions", db_index=True
    )
    from_address = models.CharField(max_length=44, db_index=True)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions_sent",
    )
    to_address = models.CharField(max_length=44, db_index=True)
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions_received",
    )
    amount = models.BigIntegerField()
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tx {self.id}: {self.amount} {self.token.symbol} from {self.from_address[:6]} to {self.to_address[:6]}"


class Favorite(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        db_index=True,
    )
    token = models.ForeignKey(
        Token, on_delete=models.CASCADE, related_name="favorited_by", db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "token"]
        indexes = [models.Index(fields=["user", "token"])]

    def __str__(self):
        return f"User {self.user_id} favorites Token {self.token_id}"


class Permission(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permissions",
        db_index=True,
    )
    token = models.ForeignKey(
        Token, on_delete=models.CASCADE, related_name="permissions", db_index=True
    )
    can_manage = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "token"]
        indexes = [models.Index(fields=["user", "token"])]

    def __str__(self):
        status = "can manage" if self.can_manage else "cannot manage"
        return f"User {self.user_id} {status} Token {self.token_id}"
