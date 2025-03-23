from django.contrib.auth import login, logout
from allauth.socialaccount.models import SocialAccount
from ..models import User

"""认证服务：处理用户认证相关的业务逻辑"""

class AuthService:
    @staticmethod
    def google_login(request, access_token):
        """处理Google OAuth登录流程
        
        Args:
            request: HTTP请求对象
            access_token: Google提供的访问令牌
            
        Returns:
            User: 登录成功返回用户对象
            None: 登录失败返回None
        """
        try:
            # 从Google获取用户信息
            social_account = SocialAccount.objects.get_or_create(
                provider='google',
                uid=access_token['sub'],
                defaults={
                    'extra_data': access_token
                }
            )[0]

            # 获取或创建用户
            user = social_account.user or User.objects.create(
                username=access_token['email'],
                email=access_token['email'],
                google_id=access_token['sub']
            )

            # 登录用户
            login(request, user)
            return user
        except Exception as e:
            print(f"Google login error: {str(e)}")
            return None

    @staticmethod
    def logout_user(request):
        try:
            logout(request)
            return True
        except Exception as e:
            print(f"Logout error: {str(e)}")
            return False
