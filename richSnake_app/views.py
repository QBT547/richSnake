from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import User, Referral, ReferredUser, Task
from .serializers import UserSerializer, ReferredUserSerializer, TaskSerializer
from django.shortcuts import get_object_or_404

@api_view(['GET', 'PUT', 'POST'])
def get_or_create_user(request, telegram_id):

    if request.method  == 'GET':
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({'message':'User not found'})

        serializer = UserSerializer(user)
        return Response({'user':serializer.data})
        
    elif request.method == 'PUT':
        user, created = User.objects.get_or_create(telegram_id=telegram_id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message':'User updated', 'user':serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        referral_code = request.data.get('referral_code')
    
        try:
            referrer = Referral.objects.get(referral_code=referral_code).user
        except Referral.DoesNotExist:
            return Response({'error': 'Invalid referral code'}, status=status.HTTP_400_BAD_REQUEST)

        new_user, created = User.objects.get_or_create(telegram_id=telegram_id)
        if created:
            referral = Referral.objects.create(user=new_user)
            ReferredUser.objects.create(referred_by=referrer.referral, referred_user=new_user)
            referrer.score += 10
            referrer.save()
            return Response({'message': 'User created with referral, referrer earned 10 points'}, status=status.HTTP_201_CREATED)

        return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    
# List users referred by a specific user
@api_view(['GET'])
def get_referral_list_of_user(request, telegram_id):
    user = User.objects.get(telegram_id=telegram_id)
    referral = user.referral
    referred_users = referral.referred_users.all()

    # Get the total score a user earned from referrals.
    total_score = sum([ru.earned_score for ru in user.referral.referred_users.all()])

    # List users referred by a specific user
    serializer = ReferredUserSerializer(referred_users, many=True)
    return Response({
        'referred_users': serializer.data,
        'total_referral_score': total_score,
        # and get refferal code of that user
        "referral_code_of_user":user.referral.referral_code
    })


# get task list
@api_view(['GET','POST'])
def get_mark_as_done_tasks(request, telegram_id):
    if request.method == 'GET':
        # Get the user or return a 404 if not found
        user = get_object_or_404(User, telegram_id=telegram_id)
        
        # Retrieve completed tasks
        completed_tasks = Task.objects.filter(task_users__user=user)
        
        # Retrieve incomplete tasks
        incomplete_tasks = Task.objects.exclude(id__in=completed_tasks.values_list('id', flat=True))

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

        # Mark Task as Done
        # Mark the task as completed by the user and update the score.
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

            return Response({'message': 'Task completed successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

