from django.urls import path
from .views import (get_or_create_user, get_referral_list_of_user,
                    get_mark_as_done_tasks,auth_view, get_prizes_list,
                    leaderboard_list) # Import the view function here

urlpatterns = [
    path('user/', get_or_create_user, name='get_or_create_user'),  # Correctly reference the view here
    path('referred/', get_referral_list_of_user, name='get_referral_list_of_user'),
    path('get_mark_as_done_tasks/',get_mark_as_done_tasks, name='get_mark_as_done_tasks'),
    path('auth_view/', auth_view, name='auth_view'),
    path('get_prizes_list/',get_prizes_list, name='get_prizes_list'),
    path('leaderboard_list/',leaderboard_list,name='leaderboard_list')
]