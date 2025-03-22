from rest_framework import serializers

class AccountSerializer(serializers.Serializer):
    wallet_address = serializers.CharField(max_length=42)
    created_at = serializers.DateTimeField()
    balance = serializers.FloatField()
    spl_tokens = serializers.ListField(child=serializers.DictField())
    recent_transactions = serializers.ListField(child=serializers.DictField())

class TransactionSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(max_length=64)
    timestamp = serializers.DateTimeField()
    transaction_type = serializers.ChoiceField(choices=['send', 'receive', 'token_transfer', 'nft_trade'])
    amount = serializers.FloatField()
    token = serializers.CharField(max_length=20, allow_blank=True)

class AssetSerializer(serializers.Serializer):
    token_name = serializers.CharField(max_length=50)
    token_logo = serializers.URLField()
    quantity = serializers.FloatField()
    value = serializers.FloatField()

class NFTSerializer(serializers.Serializer):
    nft_name = serializers.CharField(max_length=100)
    nft_image = serializers.URLField()
    metadata = serializers.JSONField()