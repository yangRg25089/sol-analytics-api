from rest_framework import serializers

from core.models import Favorite, Permission, Token, Transaction, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "user_type",
            "google_id",
            "email",
            "solana_address",
            "name",
            "avatar_url",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "id", "user_type")


class TokenSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="owner"
    )
    is_favorite = serializers.SerializerMethodField()
    favorited_count = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = (
            "id",
            "name",
            "symbol",
            "total_supply",
            "owner",
            "owner_id",
            "is_active",
            "created_at",
            "updated_at",
            "is_favorite",
            "favorited_count",
        )
        read_only_fields = ("created_at", "updated_at", "id", "owner")

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            try:
                return Favorite.objects.filter(
                    user_id=request.user.id, token=obj
                ).exists()
            except AttributeError:
                return False
        return False

    def get_favorited_count(self, obj):
        return obj.favorited_by.count()


class TransactionSerializer(serializers.ModelSerializer):
    token = TokenSerializer(read_only=True)
    token_id = serializers.PrimaryKeyRelatedField(
        queryset=Token.objects.all(), write_only=True, source="token"
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "token",
            "token_id",
            "from_address",
            "to_address",
            "amount",
            "timestamp",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "id", "token")


class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    token = TokenSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="user"
    )
    token_id = serializers.PrimaryKeyRelatedField(
        queryset=Token.objects.all(), write_only=True, source="token"
    )

    class Meta:
        model = Favorite
        fields = (
            "id",
            "user",
            "user_id",
            "token",
            "token_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "id", "user", "token")

    def validate(self, attrs):
        return attrs


class PermissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    token = TokenSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="user"
    )
    token_id = serializers.PrimaryKeyRelatedField(
        queryset=Token.objects.all(), write_only=True, source="token"
    )

    class Meta:
        model = Permission
        fields = (
            "id",
            "user",
            "user_id",
            "token",
            "token_id",
            "can_manage",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "id", "user", "token")
