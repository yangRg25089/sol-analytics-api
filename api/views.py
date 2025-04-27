"""
视图模块：处理所有API请求的核心逻辑
包含：认证、钱包连接、代币管理等功能
"""

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout # 导入 logout

# 更新导入 (回到 .serializers, core.models)
from .serializers import UserSerializer, TokenSerializer, TransactionSerializer, FavoriteSerializer, PermissionSerializer
from core.models import User, Token, Transaction, Favorite, Permission # Correct import path
from .services.market_service import MarketService
from .services.wallet_service import WalletService
from .services.token_service import TokenService
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from decimal import Decimal, InvalidOperation
from django.utils import timezone

# 自定义权限类 (示例)
class IsTokenManager(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Token):
            if not hasattr(request.user, 'id'):
                 return False 
            has_perm = Permission.objects.filter(user_id=request.user.id, token=obj, can_manage=True).exists()
            is_owner_issuer = (request.user.role in ['token_issuer', 'admin']) and (obj.owner_id == request.user.id)
            return has_perm or is_owner_issuer
        return False

# 用户认证相关视图集
class AuthViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'get_user':
            return [IsAuthenticated()]
        if self.action == 'logout':
            return [IsAuthenticated()]
        return []

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'status': 'Successfully logged out.'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='me')
    def get_user(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# 钱包绑定相关视图
class WalletViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def connect(self, request):
        solana_address = request.data.get('solana_address')
        if not solana_address:
            return Response({'error': 'Solana address is required'}, status=400)
        
        wallet_service = WalletService()
        if wallet_service.connect_wallet(request.user, solana_address):
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        return Response({'error': 'Invalid wallet address or failed to save'}, status=400)

# 代币管理视图集
class TokenViewSet(viewsets.ModelViewSet):
    serializer_class = TokenSerializer
    queryset = Token.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'market_list', 'history']:
            return []
        if self.action in ['favorite', 'unfavorite']:
            return [IsAuthenticated()]
        if self.action in ['manage', 'update', 'partial_update', 'destroy']:
            # return [IsTokenManager()]
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(detail=False, methods=['post'], url_path='market-list')
    def market_list(self, request):
        vs_currency = request.data.get('vs_currency', 'usd')
        page = int(request.data.get('page', 1))
        per_page = int(request.data.get('per_page', 20))
        market_service = MarketService()
        result = market_service.get_top_tokens(vs_currency=vs_currency, page=page, per_page=per_page)
        return Response(result)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        token = self.get_object()
        if not hasattr(request.user, 'id'):
            return Response({"error": "User not authenticated properly"}, status=401)
        favorite, created = Favorite.objects.get_or_create(
            user_id=request.user.id,
            token=token
        )
        if created:
            return Response({'status': 'token favorited'})
        else:
            return Response({'status': 'token already favorited'})

    @action(detail=True, methods=['post'])
    def unfavorite(self, request, pk=None):
        token = self.get_object()
        if not hasattr(request.user, 'id'):
            return Response({"error": "User not authenticated properly"}, status=401)
        deleted_count, _ = Favorite.objects.filter(
            user_id=request.user.id,
            token=token
        ).delete()
        if deleted_count > 0:
            return Response({'status': 'token unfavorited'})
        else:
            return Response({'status': 'token was not favorited'})

    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        token = self.get_object()
        to_address = request.data.get('to_address')
        amount = request.data.get('amount')

        if not request.user.solana_address:
             return Response({'error': 'User has no Solana address connected'}, status=400)
        if not to_address or not amount:
            return Response({'error': 'Missing to_address or amount'}, status=400)

        serializer = TransactionSerializer(data={
            'token_id': token.id,
            'from_address': request.user.solana_address,
            'from_user_id': request.user.id,
            'to_address': to_address,
            'amount': amount,
            'timestamp': timezone.now()
        }, context=self.get_serializer_context())

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        token = self.get_object()
        transactions = Transaction.objects.filter(token=token).order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def manage(self, request, pk=None):
        token = self.get_object()
        if not hasattr(request.user, 'id'):
            return Response({"error": "User not authenticated properly"}, status=401)
            
        # if not IsTokenManager().has_object_permission(request, self, token):
        #     return Response({'error': 'Permission denied'}, status=403)
        if token.owner_id != request.user.id and request.user.role not in ['admin', 'token_issuer']:
             return Response({'error': 'Permission denied. Not owner or manager.'}, status=403)

        action_type = request.data.get('action')
        amount = request.data.get('amount')

        if not action_type or not amount:
            return Response({'error': 'Missing action or amount'}, status=400)

        try:
            amount_decimal = Decimal(amount)
        except InvalidOperation:
             return Response({'error': 'Invalid amount'}, status=400)

        try:
            token_service = TokenService()
            updated_token = token_service.manage_token_supply(
                token=token,
                user=request.user,
                action_type=action_type,
                amount=amount_decimal
            )
            serializer = self.get_serializer(updated_token)
            return Response(serializer.data)
        except (ValueError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            print(f"Error during token management: {e}")
            return Response({'error': 'Internal server error during token management'}, status=500)

# ... (rest of the file, e.g., commented out FavoriteViewSet) 