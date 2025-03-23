from decimal import Decimal
from django.core.exceptions import PermissionDenied

"""代币服务：处理代币相关的业务逻辑"""

class TokenService:
    @staticmethod
    def manage_token_supply(token, user, action_type, amount):
        """管理代币供应量（增发/销毁）
        
        Args:
            token: 代币对象
            user: 操作用户
            action_type: 操作类型（'mint'或'burn'）
            amount: 操作数量
            
        Raises:
            PermissionDenied: 权限不足
            ValueError: 参数错误或余额不足
            
        Returns:
            Token: 更新后的代币对象
        """
        if not user.is_staff or token.owner != user:
            raise PermissionDenied("No permission to manage this token")

        amount = Decimal(str(amount))
        if action_type == 'mint':
            token.total_supply += amount
        elif action_type == 'burn':
            if token.total_supply >= amount:
                token.total_supply -= amount
            else:
                raise ValueError("Insufficient supply")
        else:
            raise ValueError("Invalid action type")

        token.save()
        return token
