from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Circle, Membership, Round

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
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Membership
        fields = ['id', 'user_id', 'username', 'position', 'paid_out']


class RoundSerializer(serializers.ModelSerializer):
    member_statuses = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = ['id', 'round_number', 'status', 'deadline', 'recipient', 'final_payout_amount', 'approved_at', 'member_statuses']

    def get_member_statuses(self, round_obj):
        contributed_ids = set(round_obj.contributions.values_list('member_id', flat=True))
        statuses = []
        for membership in round_obj.circle.memberships.all():
            if membership.id == round_obj.recipient_id:
                member_status = 'recipient'
            elif membership.id in contributed_ids:
                member_status = 'contributed'
            else:
                member_status = 'waiting'
            statuses.append({'membership_id': membership.id, 'status': member_status})
        return statuses


class CircleSerializer(serializers.ModelSerializer):
    members = MembershipSerializer(source='memberships', many=True, read_only=True)
    admin = serializers.IntegerField(source='admin_id', read_only=True)
    current_round = serializers.SerializerMethodField()

    class Meta:
        model = Circle
        fields = ['id', 'name', 'invite_code', 'contribution_amount', 'penalty_rate', 'created_at', 'admin', 'members', 'current_round']
        read_only_fields = ['id', 'invite_code', 'created_at', 'members', 'admin', 'current_round']

    def get_current_round(self, circle):
        current_round = circle.rounds.order_by('-round_number').first()
        if current_round is None:
            return None
        return RoundSerializer(current_round).data
