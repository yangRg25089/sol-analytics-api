from rest_framework import viewsets, generics
from rest_framework.response import Response
from .serializers import AccountSerializer, TransactionSerializer
from .models import Account, Transaction, TokenHolding, NFTHolding, TokenPrice
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

class AccountViewSet(viewsets.ViewSet):
    def retrieve(self, request, wallet_address=None):
        account = Account.objects.get(wallet_address=wallet_address)
        serializer = AccountSerializer(account)
        return Response(serializer.data)

class TransactionViewSet(viewsets.ViewSet):
    def list(self, request, wallet_address=None):
        transactions = Transaction.objects.filter(wallet_address=wallet_address)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class AssetsView(generics.ListAPIView):
    def get(self, request, wallet_address):
        try:
            account = Account.objects.get(wallet_address=wallet_address)
            
            # Get both token and NFT holdings
            tokens = TokenHolding.objects.filter(wallet_address=account)
            nfts = NFTHolding.objects.filter(wallet_address=account)
            
            assets_data = {
                'tokens': [{
                    'token_address': token.token_address,
                    'token_symbol': token.token_symbol,
                    'amount': token.amount,
                    'value_usd': token.value_usd,
                    'last_updated': token.updated_at
                } for token in tokens],
                'nfts': [{
                    'mint_address': nft.mint_address,
                    'name': nft.nft_name,
                    'image_url': nft.image_url,
                    'last_updated': nft.updated_at
                } for nft in nfts]
            }
            
            return Response({
                'wallet_address': wallet_address,
                'tokens_count': len(assets_data['tokens']),
                'nfts_count': len(assets_data['nfts']),
                'assets': assets_data
            })
            
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)

class PerformanceView(generics.RetrieveAPIView):
    def get(self, request, wallet_address):
        try:
            account = Account.objects.get(wallet_address=wallet_address)
            
            # Get time range from query params (default to last 30 days)
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Get transactions within time range
            transactions = Transaction.objects.filter(
                wallet_address=account,
                block_time__gte=start_date
            )
            
            # Calculate performance metrics
            total_transactions = transactions.count()
            total_volume = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Get current portfolio value
            tokens = TokenHolding.objects.filter(wallet_address=account)
            current_portfolio_value = sum(token.value_usd for token in tokens)
            
            return Response({
                'wallet_address': wallet_address,
                'period_days': days,
                'total_transactions': total_transactions,
                'total_volume': total_volume,
                'current_portfolio_value': current_portfolio_value,
                'last_updated': account.last_checked
            })
            
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)
        except ValueError:
            return Response({'error': 'Invalid parameters'}, status=400)

class AccountOverviewView(generics.RetrieveAPIView):
    def get(self, request, wallet_address):
        try:
            account = Account.objects.get(wallet_address=wallet_address)
            
            # Get token holdings
            tokens = TokenHolding.objects.filter(wallet_address=account)
            
            # Get recent transactions
            recent_transactions = Transaction.objects.filter(
                wallet_address=account,
                block_time__gte=timezone.now() - timedelta(days=7)
            )[:10]
            
            return Response({
                'wallet_address': account.wallet_address,
                'sol_balance': account.sol_balance,
                'tokens_count': tokens.count(),
                'recent_transactions_count': recent_transactions.count(),
                'last_checked': account.last_checked
            })
            
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)

class TransactionHistoryView(generics.ListAPIView):
    def get(self, request, wallet_address):
        try:
            account = Account.objects.get(wallet_address=wallet_address)
            
            # Get query parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            transaction_type = request.query_params.get('type')
            
            # Base query
            transactions = Transaction.objects.filter(wallet_address=account)
            
            # Apply type filter if specified
            if transaction_type:
                transactions = transactions.filter(tx_type=transaction_type)
            
            # Calculate pagination
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get paginated transactions
            paginated_transactions = transactions[start:end]
            
            # Prepare response data
            transaction_data = [{
                'signature': tx.signature,
                'type': tx.tx_type,
                'amount': tx.amount,
                'timestamp': tx.block_time,
            } for tx in paginated_transactions]
            
            return Response({
                'total_count': transactions.count(),
                'page': page,
                'page_size': page_size,
                'transactions': transaction_data
            })
            
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)
        except ValueError:
            return Response({'error': 'Invalid pagination parameters'}, status=400)