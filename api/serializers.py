from rest_framework import serializers
from .models import User, Token, Transaction, Favorite

class UserSerializer(serializers.ModelSerializer):
    owned_tokens = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    favorites = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'google_id', 'solana_address', 
                 'created_at', 'updated_at', 'owned_tokens', 'favorites']
        read_only_fields = ['created_at', 'updated_at']

class TokenSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    favorited_count = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = ['id', 'name', 'symbol', 'total_supply', 'owner', 
                 'created_at', 'updated_at', 'is_favorite', 'favorited_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, token=obj).exists()
        return False

    def get_favorited_count(self, obj):
        return obj.favorited_by.count()

class TransactionSerializer(serializers.ModelSerializer):
    token = TokenSerializer(read_only=True)
    token_id = serializers.PrimaryKeyRelatedField(
        queryset=Token.objects.all(), 
        write_only=True,
        source='token'
    )

    class Meta:
        model = Transaction
        fields = ['id', 'token', 'token_id', 'from_address', 'to_address',
                 'amount', 'timestamp', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    token = TokenSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'token', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        user = self.context['request'].user
        token = attrs['token']
        if Favorite.objects.filter(user=user, token=token).exists():
            raise serializers.ValidationError("This token is already favorited.")
        return attrs