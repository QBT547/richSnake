from django.urls import path
from .views import (get_or_create_user, get_referral_list_of_user,
                    get_mark_as_done_tasks,auth_view) # Import the view function here

urlpatterns = [
    path('user/', get_or_create_user, name='get_or_create_user'),  # Correctly reference the view here
    path('referred/', get_referral_list_of_user, name='get_referral_list_of_user'),
    path('get_mark_as_done_tasks/',get_mark_as_done_tasks, name='get_mark_as_done_tasks'),
    path('auth_view/', auth_view, name='auth_view')
]