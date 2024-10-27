from django.urls import path
from .views import (get_or_create_user, get_referral_list_of_user,
                    get_mark_as_done_tasks,auth_view) # Import the view function here

urlpatterns = [
    path('user/<str:telegram_id>/', get_or_create_user, name='get_or_create_user'),  # Correctly reference the view here
    path('referred/<str:telegram_id>/', get_referral_list_of_user, name='get_referral_list_of_user'),
    path('get_mark_as_done_tasks/<str:telegram_id>/',get_mark_as_done_tasks, name='get_mark_as_done_tasks'),
    path('auth_view/', auth_view, name='auth_view')
]