from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'tokens', views.TokenViewSet, basename='tokens')
router.register(r'wallet', views.WalletViewSet, basename='wallet')

urlpatterns = [
    path('', include(router.urls)),
]