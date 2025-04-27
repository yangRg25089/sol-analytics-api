from django.db import transaction
from django.core.exceptions import PermissionDenied
from core.models import Token, Transaction, User, Permission # Correct import path
from decimal import Decimal

"""代币服务：处理代币相关的业务逻辑"""

class TokenService:
    @staticmethod
    def manage_token_supply(token, user, action_type, amount):
        """管理代币供应量（增发/销毁）
        
        Args:
            token (Token): 代币对象
            user (User): 操作用户
            action_type (str): 操作类型（'mint'或'burn'）
            amount (Decimal): 操作数量
            
        Raises:
            PermissionDenied: 权限不足
            ValueError: 参数错误或余额不足
            
        Returns:
            Token: 更新后的代币对象
        """
        # 权限检查：必须是代币所有者且角色为 token_issuer/admin，或者有 Permission 记录
        has_perm = Permission.objects.filter(user=user, token=token, can_manage=True).exists()
        is_owner_issuer = (user.role in ['token_issuer', 'admin']) and (token.owner == user)
        
        if not (has_perm or is_owner_issuer):
            raise PermissionDenied("No permission to manage this token supply.")

        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except: # noqa
                raise ValueError("Invalid amount format")
        
        if amount <= 0:
             raise ValueError("Amount must be positive")

        with transaction.atomic(): # 确保数据库操作原子性
            # 重新获取 token 对象加锁，防止并发问题
            token_locked = Token.objects.select_for_update().get(pk=token.pk)

            if action_type == 'mint':
                token_locked.total_supply += int(amount) # 模型字段是 BigIntegerField
            elif action_type == 'burn':
                if token_locked.total_supply >= int(amount):
                    token_locked.total_supply -= int(amount)
                else:
                    raise ValueError("Insufficient supply to burn")
            else:
                raise ValueError("Invalid action type. Must be 'mint' or 'burn'.")

            token_locked.save()
            # 可以考虑添加一条 Transaction 记录来审计此操作
            # Transaction.objects.create(...) 
            
        return token_locked # 返回更新后的对象
