from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponseRedirect
from django.conf import settings

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    自定义社交账户适配器，处理Google登录
    """
    def populate_user(self, request, sociallogin, data):
        """
        自定义用户创建逻辑，确保正确处理 google_id
        """
        user = super().populate_user(request, sociallogin, data)
        
        # 从 Google 账号获取用户信息
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            user.google_id = extra_data.get('sub')
            
            # 如果用户名未设置，使用邮箱作为用户名
            if not user.username:
                user.username = extra_data.get('email', '')
            
            # 如果邮箱未设置，从 extra_data 获取
            if not user.email:
                user.email = extra_data.get('email', '')
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        保存用户时确保 google_id 的唯一性
        """
        user = super().save_user(request, sociallogin, form)
        
        if sociallogin.account.provider == 'google':
            # 检查是否已存在具有相同 google_id 的用户
            existing_user = User.objects.filter(google_id=user.google_id).first()
            if existing_user and existing_user != user:
                # 如果存在，返回现有用户
                return existing_user
        
        return user

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    自定义账户适配器，处理重定向和JWT token
    """
    def get_login_redirect_url(self, request):
        """
        重写登录重定向URL方法，添加JWT token
        """
        redirect_url = super().get_login_redirect_url(request)
        print(f"Original redirect URL: {redirect_url}")

        user = request.user
        if user.is_authenticated:
            # 生成 JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # 构造跳转地址
            return f"{redirect_url}?token={access_token}"
        return redirect_url