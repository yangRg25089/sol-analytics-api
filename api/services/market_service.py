import requests
try:
    from solana.rpc.api import Client
except ImportError:
    from solana.rpc import Client  # 使用新版本的导入路径
from django.conf import settings

"""市场服务：处理代币市场数据的获取和处理"""

class MarketService:
    def __init__(self):
        """初始化Solana客户端和CoinGecko API"""
        self.solana_client = Client(settings.SOLANA_RPC_URL)
        self.coingecko_api = "https://api.coingecko.com/api/v3"

    def get_top_tokens(self, vs_currency='usd', page=1, per_page=20):
        """获取热门代币列表
        
        Args:
            vs_currency: 计价货币（默认USD）
            page: 页码（默认第1页）
            per_page: 每页数量（默认20条）
            
        Returns:
            dict: 包含分页信息和代币列表的字典
        """
        try:
            url = f"{self.coingecko_api}/coins/markets"
            params = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": False,
                "category": "solana-ecosystem"
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return {
                'page': page,
                'per_page': per_page,
                'tokens': [{
                    'token_address': token.get('id', ''),
                    'symbol': token.get('symbol', '').upper(),
                    'name': token.get('name', ''),
                    'price_usd': token.get('current_price', 0),
                    'market_cap': token.get('market_cap', 0),
                    'volume_24h': token.get('total_volume', 0),
                    'price_change_24h': token.get('price_change_percentage_24h', 0) or 0,
                    'last_updated': token.get('last_updated'),
                    'image': token.get('image', ''),
                    'ath': token.get('ath', 0),
                    'atl': token.get('atl', 0)
                } for token in response.json()]
            }
            
        except Exception as e:
            print(f"Error fetching market data: {str(e)}")
            return {'page': page, 'per_page': per_page, 'tokens': []}

    def get_token_details(self, token_address):
        """获取单个代币的详细信息
        
        Args:
            token_address: 代币地址
            
        Returns:
            dict: 代币详细信息，包括市场数据和链上数据
            None: 获取失败返回None
        """
        try:
            # 获取 CoinGecko API 详细数据
            url = f"{self.coingecko_api}/coins/{token_address}"
            response = requests.get(url)
            response.raise_for_status()
            token_data = response.json()
            
            # 获取链上数据
            onchain_data = self.get_token_onchain_data(token_address)
            
            return {
                'token_address': token_address,
                'symbol': token_data.get('symbol', '').upper(),
                'name': token_data.get('name', ''),
                'price_usd': token_data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                'market_cap': token_data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                'volume_24h': token_data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                'price_change_24h': token_data.get('market_data', {}).get('price_change_percentage_24h', 0),
                'description': token_data.get('description', {}).get('en', ''),
                'homepage': token_data.get('links', {}).get('homepage', []),
                'image': token_data.get('image', {}).get('large', ''),
                'onchain_data': onchain_data
            }
            
        except Exception as e:
            print(f"Error fetching token details: {str(e)}")
            return None

    def get_token_onchain_data(self, token_address):
        try:
            response = self.solana_client.get_token_supply(token_address)
            if response["result"]["value"]:
                return {
                    "total_supply": response["result"]["value"]["amount"],
                    "decimals": response["result"]["value"]["decimals"]
                }
        except Exception as e:
            print(f"Error fetching onchain data: {str(e)}")
            return None
