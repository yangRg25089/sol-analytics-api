import base64
import json
import logging
from datetime import timedelta

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
            user.last_login = timezone.now()

        return user

    def save_user(self, request, sociallogin, form=None):
        """
        保存或获取用户，确保 google_id 的唯一性，并更新用户信息
        """
        try:
            # 首先尝试通过 google_id 查找用户
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
            try:
                # 如果通过 google_id 没找到，尝试通过 email 查找
                if sociallogin.account.provider == "google":
                    email = sociallogin.account.extra_data.get("email")
                    if email:
                        existing_user = User.objects.get(email=email)
                        # 更新 google_id
                        existing_user.google_id = sociallogin.account.uid
                        existing_user.user_type = "google"
                        existing_user.save()
                        sociallogin.user = existing_user
                        logger.info(f"Existing user connected to Google: {email}")
                        return existing_user
            except User.DoesNotExist:
                # 如果都不存在，创建新用户
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
            # 首先尝试通过 google_id 查找
            user = User.objects.get(google_id=sociallogin.account.uid)
            if not sociallogin.is_existing:
                sociallogin.connect(request, user)
                logger.info(f"Connected existing user to social account: {user.email}")
        except User.DoesNotExist:
            try:
                # 如果通过 google_id 没找到，尝试通过 email 查找
                if sociallogin.account.provider == "google":
                    email = sociallogin.account.extra_data.get("email")
                    if email:
                        user = User.objects.get(email=email)
                        if not sociallogin.is_existing:
                            sociallogin.connect(request, user)
                            logger.info(
                                f"Connected existing user by email to social account: {email}"
                            )
            except User.DoesNotExist:
                logger.info(
                    f"New social login attempt for google_id: {sociallogin.account.uid}"
                )
                pass


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    自定义账户适配器，处理登录重定向和JWT生成
    """

    def _encode_user_info(self, user_info):
        """
        将用户信息编码为base64字符串
        """
        json_str = json.dumps(user_info)
        return base64.urlsafe_b64encode(json_str.encode()).decode()

    def _get_error_url(self, frontend_url, error_code, error_message=None):
        """
        生成错误重定向URL
        """
        error_data = {
            "code": error_code,
            "message": error_message or self._get_error_message(error_code),
        }
        encoded_error = self._encode_user_info(error_data)
        return f"{frontend_url}/login?error={encoded_error}"

    def _get_error_message(self, error_code):
        """
        获取错误消息
        """
        error_messages = {
            "token_generation_failed": "Token generation failed",
            "authentication_failed": "Authentication failed",
            "invalid_user": "Invalid user information",
            "server_error": "Internal server error",
        }
        return error_messages.get(error_code, "Unknown error")

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
                    "role": getattr(user, "role", None),
                    "user_type": user.user_type,
                    "tokens": {
                        "access": access_token,
                        "refresh": refresh_token,
                        "access_expires_in": int(
                            settings.SIMPLE_JWT.get(
                                "ACCESS_TOKEN_LIFETIME", timedelta(minutes=5)
                            ).total_seconds()
                        ),
                        "refresh_expires_in": int(
                            settings.SIMPLE_JWT.get(
                                "REFRESH_TOKEN_LIFETIME", timedelta(days=1)
                            ).total_seconds()
                        ),
                    },
                }

                # 编码用户信息
                encoded_user_info = self._encode_user_info(user_info)

                # 构造重定向URL
                redirect_url = (
                    f"{frontend_url}{oauth_success_path}?data={encoded_user_info}"
                )

                logger.info(f"Successful login redirect for user: {user.email}")
                return redirect_url

            except Exception as e:
                logger.error(f"Error generating token for user {user.id}: {str(e)}")
                return self._get_error_url(
                    frontend_url, "token_generation_failed", str(e)
                )

        logger.warning(f"Failed authentication attempt for request: {request}")
        return self._get_error_url(frontend_url, "authentication_failed")
