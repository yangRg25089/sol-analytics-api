from django.urls import path
from . import views

urlpatterns = [
    path('account/<str:wallet_address>/', views.AccountOverviewView.as_view(), name='account_overview'),
    path('transactions/<str:wallet_address>/', views.TransactionHistoryView.as_view(), name='transaction_history'),
    path('assets/<str:wallet_address>/', views.AssetsView.as_view(), name='assets'),
    path('performance/<str:wallet_address>/', views.PerformanceView.as_view(), name='performance'),
]