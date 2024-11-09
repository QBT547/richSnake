from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from richSnake_app.helpers import get_telegram_user_photo, validate_init_data
from .models import User, Referral, ReferredUser, Task, UserTask, Prize
from .serializers import UserSerializer, ReferredUserSerializer, TaskSerializer, PrizeSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authtoken.models import Token
import time
import urllib.parse
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.files.base import ContentFile

# Create update user, create token for user, create refferal code for user
@csrf_exempt
@api_view(['POST'])
def auth_view(request):
    if request.method == "POST":
        init_data = request.data.get("initData", "")
        BOT_TOKEN = settings.BOT_TOKEN
        print(BOT_TOKEN)

        # Parse initData and extract hash and data
        parsed_data = dict(urllib.parse.parse_qsl(init_data))

        auth_date = int(parsed_data.get("auth_date", 0))
        if time.time() - auth_date > 86400:  # 1-day expiry
            return JsonResponse({"error": "Session expired"}, status=403)

        if not validate_init_data(init_data, BOT_TOKEN):
            return JsonResponse({"error": "Invalid authentication data"}, status=403)

        # Auth data verified, process user info securely
        user_data = json.loads(parsed_data['user'])

        # Extract the id
        telegram_id = user_data.get("id")
        first_name = user_data.get("first_name", "")
        username = user_data.get("username", "")

        # Fetch user's avatar photo
        avatar_url = get_telegram_user_photo(telegram_id, BOT_TOKEN)

        # Update or create user in the database with avatar URL
        user, user_created = User.objects.update_or_create(
            telegram_id=telegram_id,
            defaults={
                "first_name": first_name,
                "username": username,
            }
        )
        if avatar_url != None:
            response = requests.get(avatar_url)
            if response.status_code == 200:
                # Use a unique name for the file to avoid conflicts
                avatar_filename = f"{telegram_id}_avatar.jpg"
                user.avatar.save(avatar_filename, ContentFile(response.content), save=True)

        referral_code = parsed_data.get("start_param")
        if referral_code:
            try:
                # Find referrer based on referral_code
                referrer = Referral.objects.get(referral_code=referral_code).user
                if user_created:
                    # Create referral and referred user records
                    referral = Referral.objects.create(user=user)
                    ReferredUser.objects.create(referred_by=referrer.referral, referred_user=user)
                    referrer.score += 1000
                    referrer.save()

                    # Create a token for the user
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({
                        'message': 'User created with referral, referrer earned 10 points, token also created',
                        "token": token.key
                    }, status=status.HTTP_201_CREATED)

            except Referral.DoesNotExist:
                return Response({'error': 'Invalid referral code'}, status=status.HTTP_400_BAD_REQUEST)

        elif user_created:
            referral = Referral.objects.create(user=user)

        # Generate a token (for example, a random string here)
        token, created = Token.objects.get_or_create(user=user)

        return JsonResponse({"token": token.key, "is_new_user": user_created})

    return JsonResponse({"error": "Invalid request"}, status=400)


# get Logged User (Home page)
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_or_create_user(request):
    if request.method == 'GET':
        try:
            user = User.objects.get(telegram_id=request.user.telegram_id)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "id" : user.id,
            "username" : user.username,
            "last_name" : user.last_name,
            "date_joined" : user.date_joined,
            "telegram_id" : user.telegram_id,
            "first_name" : user.first_name,
            "score" : user.score,
            "avatar": request.build_absolute_uri(user.avatar.url) if user.avatar else None,
            "balance": user.balance,
            "record": user.record
        }
        return Response(data)

# List users referred by a specific user
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_referral_list_of_user(request):
    user = request.user
    referral, created = Referral.objects.get_or_create(user=user)

    referred_users = referral.referred_users.all()
    total_score = sum([ru.earned_score for ru in referred_users])

    serializer = ReferredUserSerializer(referred_users, many=True)
    return Response({
        'referred_users': serializer.data,
        'total_referral_score': total_score,
        "referral_code_of_user": referral.referral_code
    })

# Get task list &&& Mark as Done
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_mark_as_done_tasks(request):
    if request.method == 'GET':
        user = get_object_or_404(User, telegram_id= request.user.telegram_id)

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
            user = User.objects.get(telegram_id= request.user.telegram_id)
            task = Task.objects.get(id=task_id)

            # Check if the task is already completed
            if UserTask.objects.filter(user=user, task=task).exists():
                return Response({'message': 'Task already completed'}, status=status.HTTP_400_BAD_REQUEST)

            # Create UserTask to mark task as completed
            UserTask.objects.create(user=user, task=task)

            if task.type == Task.Types.COIN:
                # Update user's score
                user.score += task.score
                user.save()
            elif task.type == Task.Types.DOLLAR:
                user.balance += task.score
                user.save()

            return Response({'message': 'Task completed and score updated'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)


# Get Prizes List &&&
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_prizes_list(request):
    prizes = Prize.objects.all()
    serializer = PrizeSerializer(prizes, many=True)

    return Response({
        'prize_list': serializer.data
    })


#  Get Leaderboard, user_rank, user

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leaderboard_list(request):
    users = User.objects.exclude(is_superuser=True).order_by('-score')[:100]
    serializer = UserSerializer(users, many=True)

    # Try to get the requesting user
    try:
        user = User.objects.get(telegram_id=request.user.telegram_id)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Calculate user rank in the complete ordered queryset
    full_ordered_users = User.objects.order_by('-score')
    user_rank = list(full_ordered_users).index(user) + 1

    # Serialize the user's data
    user_serializer = UserSerializer(user)

    return Response({
        'leaderBoard': serializer.data,
        'user_rank': user_rank,
        'user': user_serializer.data
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user_score(request):
    user = User.objects.get(telegram_id=request.user.telegram_id)
    score_to_add = request.data.get('score', 0)
    user.score += float(score_to_add)
    if score_to_add > user.record:
        user.record = score_to_add
    user.save()
    return Response({'message': 'User score updated', 'new_score': user.score})
