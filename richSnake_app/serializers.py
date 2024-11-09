from rest_framework import serializers
from .models import User, Referral, ReferredUser, Task, Prize


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'score', 'balance', 'avatar']


class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = '__all__'


class ReferredUserSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='referred_user.username')
    image = serializers.ImageField(source='referred_user.avatar')
    coin = serializers.IntegerField(source='earned_score')

    class Meta:
        model = ReferredUser
        fields = ['user', 'coin', 'image']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prize
        fields = '__all__'