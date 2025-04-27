from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import User


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    自定义社交账户适配器，处理Google登录和用户信息填充
    """

    def populate_user(self, request, sociallogin, data):
        """
        使用从 Google 获取的数据填充自定义 User 模型字段
        """
        user = User()  # 创建我们自定义的 User 实例
        user.google_id = sociallogin.account.uid  # 使用社交账户的 uid 作为 google_id

        if sociallogin.account.provider == "google":
            extra_data = sociallogin.account.extra_data
            user.name = extra_data.get("name", "")
            user.avatar_url = extra_data.get("picture", "")
            # 可以根据需要设置 email (如果 User 模型有 email 字段)
            # user.email = extra_data.get('email')
            # 注意：我们没有 username 字段了

        # sociallogin.user = user # 这行可能不需要，因为 allauth 会处理关联
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        保存或获取用户，确保 google_id 的唯一性
        """
        # 尝试获取具有相同 google_id 的现有用户
        try:
            existing_user = User.objects.get(google_id=sociallogin.account.uid)
            # 如果用户已存在，直接返回，allauth 会处理登录
            sociallogin.user = existing_user  # 关联到找到的用户
            # 更新用户信息（可选）
            # existing_user.name = sociallogin.account.extra_data.get('name', existing_user.name)
            # existing_user.avatar_url = sociallogin.account.extra_data.get('picture', existing_user.avatar_url)
            # existing_user.save()
            return existing_user
        except User.DoesNotExist:
            # 用户不存在，创建新用户
            user = sociallogin.user  # 这是 populate_user 返回的实例
            user.google_id = sociallogin.account.uid  # 确保 google_id 设置正确
            user.set_unusable_password()  # 由于我们不使用密码登录
            user.full_clean()  # 验证模型字段
            user.save()  # 保存新用户
            sociallogin.user.save()  # 确保 sociallogin user 也被保存
            return user

    def pre_social_login(self, request, sociallogin):
        """
        在社交登录过程早期执行，尝试查找或创建用户
        """
        # 检查用户是否已存在
        try:
            user = User.objects.get(google_id=sociallogin.account.uid)
            # 如果用户已存在，但未连接到此社交账户，则连接
            if not sociallogin.is_existing:
                sociallogin.connect(request, user)
        except User.DoesNotExist:
            # 用户不存在，允许 allauth 继续创建流程
            pass


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    自定义账户适配器，主要处理重定向
    """

    def get_login_redirect_url(self, request):
        """
        重写登录重定向URL方法，携带JWT token重定向到前端
        """
        # 不再依赖 settings.LOGIN_REDIRECT_URL
        frontend_url = (
            settings.FRONTEND_BASE_URL
            if hasattr(settings, "FRONTEND_BASE_URL")
            else "http://127.0.0.1:3000"
        )
        oauth_success_path = "/oauth-success"  # 前端处理 OAuth 成功的路径

        user = request.user
        if hasattr(user, "is_authenticated") and user.is_authenticated:
            try:
                # 生成 JWT token
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                # 构造带 token 的最终跳转地址
                return f"{frontend_url}{oauth_success_path}?token={access_token}"
            except Exception as e:
                # 处理生成 token 失败的情况
                print(f"Error generating token for user {user.id}: {e}")
                # 可以重定向到一个错误页面或不带 token 的默认页面
                return (
                    f"{frontend_url}{oauth_success_path}?error=token_generation_failed"
                )

        # 如果用户未认证或发生其他问题，重定向到前端主页或登录页
        return f"{frontend_url}/login?error=authentication_failed"  # 如果用户未认证或发生其他问题，重定向到前端主页或登录页
