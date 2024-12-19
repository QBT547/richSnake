from django.urls import path
from .views import *  # Import the view function here

urlpatterns = [
    path('user/', get_or_create_user, name='get_or_create_user'),  # Correctly reference the view here
    path('referred/', get_referral_list_of_user, name='get_referral_list_of_user'),
    path('get_mark_as_done_tasks/', get_mark_as_done_tasks, name='get_mark_as_done_tasks'),
    path('auth_view/', auth_view, name='auth_view'),
    path('get_prizes_list/', get_prizes_list, name='get_prizes_list'),
    path('leaderboard_list/', leaderboard_list, name='leaderboard_list'),
    path('prizers_list/', prizers_list, name='prizers_list'),
    path('update_user_score/', update_user_score, name='update_user_score'),
    path('update_user_score_hard/', update_user_score_hard, name='update_user_score_hard'),
    path('subscription', get_user_subscription, name='get_user_subscription'),
    path('subscription/buy', buy_subscription, name='buy_subscription'),
    path('update_wallet_address', update_wallet_address, name='update_wallet_address'),
    path('create_withdraw_request', create_withdraw_request, name='create_withdraw_request'),
    path('buy_subscription_telegram', buy_subscription_telegram, name='buy_subscription_telegram'),
    path('payment_status_webhook', payment_status_webhook, name='payment_status_webhook'),
]
