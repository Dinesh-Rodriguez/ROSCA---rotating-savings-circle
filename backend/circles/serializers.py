from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Circle, Membership

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=1)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Membership
        fields = ['username', 'position', 'paid_out']

class CircleSerializer(serializers.ModelSerializer):
    members = MembershipSerializer(source='memberships', many=True, read_only=True)
    class Meta:
        model = Circle
        fields = ['id', 'name', 'invite_code', 'contribution_amount', 'penalty_rate', 'created_at', 'members']
        read_only_fields = ['id', 'invite_code', 'created_at', 'members']
