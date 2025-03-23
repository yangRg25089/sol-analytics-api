from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'tokens', views.TokenViewSet, basename='tokens')
router.register(r'wallet', views.WalletViewSet, basename='wallet')

# 只需要使用 router 的 URLs，删除重复的路径定义
urlpatterns = [
    path('', include(router.urls)),
]