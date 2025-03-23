from solana.rpc.api import Client
from django.conf import settings

"""钱包服务：处理Solana钱包相关的操作"""

class WalletService:
    def __init__(self):
        """初始化Solana客户端连接"""
        self.client = Client(settings.SOLANA_RPC_URL)

    def verify_wallet_address(self, address):
        """验证Solana钱包地址的有效性
        
        Args:
            address: Solana钱包地址
            
        Returns:
            bool: 地址有效返回True，否则返回False
        """
        try:
            # 验证地址格式和余额
            response = self.client.get_balance(address)
            return response.get('result', {}).get('value', 0) is not None
        except Exception as e:
            print(f"Wallet verification error: {str(e)}")
            return False

    def connect_wallet(self, user, address):
        try:
            if self.verify_wallet_address(address):
                user.solana_address = address
                user.save()
                return True
            return False
        except Exception as e:
            print(f"Wallet connection error: {str(e)}")
            return False
