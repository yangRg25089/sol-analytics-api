import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import User

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    自定义社交账户适配器，处理Google登录和用户信息填充
    """

    def populate_user(self, request, sociallogin, data):
        """
        使用从 Google 获取的数据填充自定义 User 模型字段
        """
        user = super().populate_user(request, sociallogin, data)
        user.user_type = "google"
        user.google_id = sociallogin.account.uid

        if sociallogin.account.provider == "google":
            extra_data = sociallogin.account.extra_data
            user.email = extra_data.get("email")
            user.name = extra_data.get("name", "")
            user.avatar_url = extra_data.get("picture", "")
            # 更新最后登录时间
            user.last_login = timezone.now()

        return user

    def save_user(self, request, sociallogin, form=None):
        """
        保存或获取用户，确保 google_id 的唯一性，并更新用户信息
        """
        try:
            # 尝试获取具有相同 google_id 的现有用户
            existing_user = User.objects.get(google_id=sociallogin.account.uid)

            # 更新用户信息
            if sociallogin.account.provider == "google":
                extra_data = sociallogin.account.extra_data
                existing_user.email = extra_data.get("email", existing_user.email)
                existing_user.name = extra_data.get("name", existing_user.name)
                existing_user.avatar_url = extra_data.get(
                    "picture", existing_user.avatar_url
                )
                existing_user.last_login = timezone.now()
                existing_user.save()

            sociallogin.user = existing_user
            logger.info(f"Existing user logged in: {existing_user.email}")
            return existing_user

        except User.DoesNotExist:
            # 用户不存在，创建新用户
            user = sociallogin.user
            user.user_type = "google"
            user.google_id = sociallogin.account.uid
            user.set_unusable_password()

            try:
                user.full_clean()
                user.save()
                sociallogin.user.save()
                logger.info(f"New user created: {user.email}")
                return user
            except Exception as e:
                logger.error(f"Error creating new user: {str(e)}")
                raise

    def pre_social_login(self, request, sociallogin):
        """
        在社交登录过程早期执行，尝试查找或创建用户
        """
        try:
            user = User.objects.get(google_id=sociallogin.account.uid)
            if not sociallogin.is_existing:
                sociallogin.connect(request, user)
                logger.info(f"Connected existing user to social account: {user.email}")
        except User.DoesNotExist:
            logger.info(
                f"New social login attempt for google_id: {sociallogin.account.uid}"
            )
            pass


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    自定义账户适配器，处理登录重定向和JWT生成
    """

    def get_login_redirect_url(self, request):
        """
        重写登录重定向URL方法，携带JWT token和用户信息重定向到前端
        """
        frontend_url = (
            settings.FRONTEND_BASE_URL
            if hasattr(settings, "FRONTEND_BASE_URL")
            else "http://127.0.0.1:3000"
        )
        oauth_success_path = "/oauth-success"

        user = request.user
        if hasattr(user, "is_authenticated") and user.is_authenticated:
            try:
                # 生成 JWT token
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # 准备用户信息
                user_info = {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "avatar_url": user.avatar_url,
                    "role": user.role,
                    "user_type": user.user_type,
                }

                # 构造重定向URL，包含token和用户信息
                redirect_url = (
                    f"{frontend_url}{oauth_success_path}"
                    f"?token={access_token}"
                    f"&refresh_token={refresh_token}"
                    f"&user_info={user_info}"
                )

                logger.info(f"Successful login redirect for user: {user.email}")
                return redirect_url

            except Exception as e:
                logger.error(f"Error generating token for user {user.id}: {str(e)}")
                return (
                    f"{frontend_url}{oauth_success_path}?error=token_generation_failed"
                )

        logger.warning(f"Failed authentication attempt for request: {request}")
        return f"{frontend_url}/login?error=authentication_failed"
