"""
视图模块：处理所有API请求的核心逻辑
包含：认证、钱包连接、代币管理等功能
"""

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, TokenSerializer, TransactionSerializer, FavoriteSerializer
from .models import User, Token, Transaction, Favorite
from .services.market_service import MarketService
from .services.auth_service import AuthService
from .services.wallet_service import WalletService
from .services.token_service import TokenService

# 用户认证相关视图集（登录、登出、获取当前用户信息）
class AuthViewSet(viewsets.ViewSet):
    """
    处理用户认证相关的视图集
    功能包括：Google登录、登出、获取用户信息
    """

    def get_permissions(self):
        """
        动态权限控制：
        - 只有 get_user 需要用户已登录
        - 其他（登录、登出）接口对所有用户开放
        """
        if self.action == 'get_user':
            return [IsAuthenticated()]
        return []

    @action(detail=False, methods=['post'])
    def google_login(self, request):
        """
        Google OAuth 登录
        接收 access_token，验证通过后返回用户信息
        """
        access_token = request.data.get('access_token')
        if not access_token:
            return Response({'error': 'Access token is required'}, status=400)
        
        auth_service = AuthService()
        user = auth_service.google_login(request, access_token)
        if user:
            serializer = UserSerializer(user)
            return Response(serializer.data)
        return Response({'error': 'Login failed'}, status=401)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        登出当前用户
        """
        auth_service = AuthService()
        if auth_service.logout_user(request):
            return Response({'status': 'success'})
        return Response({'error': 'Logout failed'}, status=400)

    @action(detail=False, methods=['get'])
    def get_user(self, request):
        """
        获取当前已登录用户的信息
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# 钱包绑定相关视图
class WalletViewSet(viewsets.ViewSet):
    """
    钱包视图集
    功能：用户绑定 Solana 钱包地址
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def connect(self, request):
        """
        用户绑定 Solana 钱包地址
        """
        solana_address = request.data.get('solana_address')
        if not solana_address:
            return Response({'error': 'Solana address is required'}, status=400)
        
        wallet_service = WalletService()
        if wallet_service.connect_wallet(request.user, solana_address):
            return Response({'status': 'success'})
        return Response({'error': 'Invalid wallet address'}, status=400)

# 代币管理视图集（列表、收藏、转账、交易历史、增发销毁）
class TokenViewSet(viewsets.ModelViewSet):
    """
    代币管理视图集
    功能包括：
    - 查看代币市场列表
    - 收藏/取消收藏代币
    - 代币转账
    - 查看交易历史（含图表）
    - 超级用户增发/销毁代币
    """
    serializer_class = TokenSerializer

    def get_queryset(self):
        """
        定义数据源（标准 ModelViewSet 必需方法）
        用于支持自动生成 RESTful API（GET/POST/PUT/DELETE）
        """
        return Token.objects.all()
    
    def get_permissions(self):
        """
        控制权限：
        - list（获取代币列表）允许匿名访问
        - 其他操作需要登录
        """
        if self.action in ['list', 'market_list']:  # 允许匿名访问的action
            return []  # 空权限 = 允许任何人访问
        return [IsAuthenticated()]  # 其他需要登录

    @action(detail=False, methods=['post'], url_path='market-list')
    def market_list(self, request):
        """
        通过 POST 获取代币市场数据（允许匿名访问）
        接收参数：
        - vs_currency
        - page
        - per_page

        自定义代币列表（主页市场数据）
        不直接返回数据库数据，而是通过 MarketService 获取链上市场数据
        """
        vs_currency = request.data.get('vs_currency', 'usd')
        page = int(request.data.get('page', 1))
        per_page = int(request.data.get('per_page', 20))

        market_service = MarketService()
        result = market_service.get_top_tokens(vs_currency=vs_currency, page=page, per_page=per_page)
        return Response(result)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """
        收藏指定代币
        """
        token = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            token=token
        )
        return Response({'status': 'token favorited'})

    @action(detail=True, methods=['post'])
    def unfavorite(self, request, pk=None):
        """
        取消收藏指定代币
        """
        token = self.get_object()
        Favorite.objects.filter(
            user=request.user,
            token=token
        ).delete()
        return Response({'status': 'token unfavorited'})

    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """
        代币转账（用户必须已绑定钱包地址）
        请求参数：
        - to_address：接收地址
        - amount：转账数量
        """
        token = self.get_object()
        serializer = TransactionSerializer(data={
            'token': token.id,
            'from_address': request.user.solana_address,
            'to_address': request.data.get('to_address'),
            'amount': request.data.get('amount')
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        获取指定代币的交易历史
        前端会结合 Chart.js 生成图表
        """
        token = self.get_object()
        transactions = Transaction.objects.filter(token=token)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def manage(self, request, pk=None):
        """
        超级用户操作代币供应（增发/销毁）
        权限：
        - 用户必须为 is_staff 且为代币创建者
        请求参数：
        - action：增发 mint / 销毁 burn
        - amount：操作数量
        """
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=403)

        token = self.get_object()
        action_type = request.data.get('action')
        amount = request.data.get('amount')

        try:
            token_service = TokenService()
            updated_token = token_service.manage_token_supply(
                token=token,
                user=request.user,
                action_type=action_type,
                amount=amount
            )
            serializer = self.get_serializer(updated_token)
            return Response(serializer.data)
        except (ValueError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': 'Internal server error'}, status=500)
