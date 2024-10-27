from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from richSnake_app.helpers import BOT_TOKEN, get_telegram_user_photo, validate_init_data
from .models import User, Referral, ReferredUser, Task, UserTask
from .serializers import UserSerializer, ReferredUserSerializer, TaskSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authtoken.models import Token
import hashlib
import hmac
import time
import urllib.parse
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string


@csrf_exempt
@api_view(['POST'])
def auth_view(request):
    if request.method == "POST":
        init_data = request.POST.get("initData", "")

        # Parse initData and extract hash and data
        parsed_data = dict(urllib.parse.parse_qsl(init_data))
        auth_date = int(parsed_data.get("auth_date", 0))
        if time.time() - auth_date > 86400:  # 1-day expiry
            return JsonResponse({"error": "Session expired"}, status=403)

        if validate_init_data(init_data, BOT_TOKEN):
            return JsonResponse({"error": "Invalid authentication data"}, status=403)

        # Auth data verified, process user info securely
        telegram_id = parsed_data["id"]
        first_name = parsed_data.get("first_name", "")
        username = parsed_data.get("username", "")

        # Fetch user's avatar photo
        avatar_url = get_telegram_user_photo(telegram_id)

        # Update or create user in the database with avatar URL
        user, created = User.objects.update_or_create(
            telegram_id=telegram_id,
            defaults={
                "first_name": first_name,
                "username": username,
                "avatar_url": avatar_url
            }
        )

        # Generate a token (for example, a random string here)
        token, created = Token.objects.get_or_create(user=user)

        return JsonResponse({"token": token.key})

    return JsonResponse({"error": "Invalid request"}, status=400)


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_or_create_user(request, telegram_id):
    if request.method == 'GET':
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response({'user': serializer.data})

    elif request.method == 'POST':
        referral_code = request.data.get('referral_code')

        try:
            referrer = Referral.objects.get(referral_code=referral_code).user
        except Referral.DoesNotExist:
            return Response({'error': 'Invalid referral code'}, status=status.HTTP_400_BAD_REQUEST)

        new_user, created = User.objects.get_or_create(telegram_id=telegram_id)
        if created:
            referral = Referral.objects.create(user=new_user)
            ReferredUser.objects.create(
                referred_by=referrer.referral, referred_user=new_user)
            referrer.score += 10
            referrer.save()
            return Response({'message': 'User created with referral, referrer earned 10 points'}, status=status.HTTP_201_CREATED)

        return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)


# List users referred by a specific user
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_referral_list_of_user(request, telegram_id):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        referral = user.referral
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Referral.DoesNotExist:
        return Response({'error': 'Referral not found'}, status=status.HTTP_404_NOT_FOUND)

    referred_users = referral.referred_users.all()
    total_score = sum([ru.earned_score for ru in referred_users])

    serializer = ReferredUserSerializer(referred_users, many=True)
    return Response({
        'referred_users': serializer.data,
        'total_referral_score': total_score,
        "referral_code_of_user": referral.referral_code
    })

# Get task list


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_mark_as_done_tasks(request, telegram_id):
    if request.method == 'GET':
        user = get_object_or_404(User, telegram_id=telegram_id)

        # Retrieve completed tasks
        completed_tasks = Task.objects.filter(task_users__user=user)

        # Retrieve incomplete tasks
        incomplete_tasks = Task.objects.exclude(
            id__in=completed_tasks.values_list('id', flat=True))

        # Serialize both completed and incomplete tasks
        completed_serializer = TaskSerializer(completed_tasks, many=True)
        incomplete_serializer = TaskSerializer(incomplete_tasks, many=True)

        # Return both lists in the response
        return Response({
            'completed_tasks': completed_serializer.data,
            'incomplete_tasks': incomplete_serializer.data
        })

    elif request.method == 'POST':
        task_id = int(request.data.get('task_id', 0))

        try:
            user = User.objects.get(telegram_id=telegram_id)
            task = Task.objects.get(id=task_id)

            # Check if the task is already completed
            if UserTask.objects.filter(user=user, task=task).exists():
                return Response({'message': 'Task already completed'}, status=status.HTTP_400_BAD_REQUEST)

            # Create UserTask to mark task as completed
            UserTask.objects.create(user=user, task=task)

            # Update user's score
            user.score += task.score
            user.save()

            return Response({'message': 'Task completed and score updated'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
