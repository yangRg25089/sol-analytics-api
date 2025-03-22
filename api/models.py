from django.db import models

class Account(models.Model):
    wallet_address = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    sol_balance = models.DecimalField(max_digits=20, decimal_places=9, default=0)

    def __str__(self):
        return self.wallet_address

class Transaction(models.Model):
    wallet_address = models.ForeignKey(Account, on_delete=models.CASCADE, to_field='wallet_address', related_name='transactions')
    signature = models.TextField(unique=True)
    block_time = models.DateTimeField()
    tx_type = models.TextField()
    token_address = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=9)
    fee = models.DecimalField(max_digits=12, decimal_places=9)
    status = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['wallet_address']),
            models.Index(fields=['signature']),
        ]
        ordering = ['-block_time']

class TokenHolding(models.Model):
    wallet_address = models.ForeignKey(Account, on_delete=models.CASCADE, to_field='wallet_address', related_name='token_holdings')
    token_address = models.TextField()
    token_symbol = models.TextField()
    amount = models.DecimalField(max_digits=30, decimal_places=9)
    value_usd = models.DecimalField(max_digits=20, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['wallet_address']),
            models.Index(fields=['token_address']),
        ]
        unique_together = ['wallet_address', 'token_address']

class NFTHolding(models.Model):
    wallet_address = models.ForeignKey(Account, on_delete=models.CASCADE, to_field='wallet_address', related_name='nft_holdings')
    mint_address = models.TextField()
    nft_name = models.TextField()
    image_url = models.TextField()
    metadata_uri = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['wallet_address']),
            models.Index(fields=['mint_address']),
        ]

class TokenPrice(models.Model):
    token_address = models.TextField()
    price_usd = models.DecimalField(max_digits=20, decimal_places=9)
    timestamp = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['token_address']),
        ]
