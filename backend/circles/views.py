from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Circle, Contribution, Membership, Round
from .serializers import CircleSerializer, LoginSerializer, MembershipSerializer, RegisterSerializer
from .utils import round_half_up


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(**serializer.validated_data)
        if user is None:
            return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username})

class CircleCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = CircleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        circle = serializer.save(admin=request.user)
        Membership.objects.create(circle=circle, user=request.user, position=1)
        return Response(CircleSerializer(circle).data, status=status.HTTP_201_CREATED)

class CircleJoinView(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request):
        code = request.data.get('invite_code')
        if not code:
            return Response({'invite_code': ['This field is required.']}, status=400)
        circle = get_object_or_404(Circle.objects.select_for_update(), invite_code=code)
        if Membership.objects.filter(circle=circle, user=request.user).exists():
            return Response({'detail': 'You are already a member of this circle.'}, status=400)
        count = Membership.objects.filter(circle=circle).count()
        if count >= 4:
            return Response({'detail': 'This circle is full.'}, status=400)
        membership = Membership.objects.create(circle=circle, user=request.user, position=count + 1)
        if count + 1 == 4:
            recipient = Membership.objects.filter(circle=circle, paid_out=False).order_by('position').first()
            Round.objects.create(circle=circle, round_number=1, recipient=recipient,
                                 deadline=timezone.now() + timedelta(days=3))
        return Response(MembershipSerializer(membership).data, status=201)

class CircleDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        circle = get_object_or_404(
            Circle.objects.prefetch_related('memberships__user', 'rounds__contributions'), pk=pk
        )
        return Response(CircleSerializer(circle).data)


class ContributionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        round_obj = get_object_or_404(Round.objects.select_for_update(), pk=pk)
        if round_obj.status != Round.Status.OPEN:
            return Response({'detail': 'This round is not open.'}, status=400)
        member = get_object_or_404(Membership, circle=round_obj.circle, user=request.user)
        if member.pk == round_obj.recipient_id:
            return Response({'detail': 'The recipient does not contribute to their own payout.'}, status=400)
        submitted_at = timezone.now()
        late = submitted_at > round_obj.deadline
        penalty = round_half_up(round_obj.circle.contribution_amount, round_obj.circle.penalty_rate) if late else 0
        try:
            contribution = Contribution.objects.create(
                round=round_obj, member=member,
                amount_owed=round_obj.circle.contribution_amount,
                amount_paid=round_obj.circle.contribution_amount + penalty,
                is_late=late, penalty=penalty, submitted_at=submitted_at,
            )
        except IntegrityError:
            return Response({'detail': 'You have already contributed to this round.'}, status=400)
        active_ids = Membership.objects.filter(circle=round_obj.circle, paid_out=False).exclude(pk=round_obj.recipient_id).values_list('pk', flat=True)
        contributed = Contribution.objects.filter(round=round_obj, member_id__in=active_ids).count()
        if contributed == len(active_ids):
            round_obj.status = Round.Status.PENDING_APPROVAL
            round_obj.save(update_fields=['status'])
        return Response({'id': contribution.id, 'amount_paid': contribution.amount_paid, 'penalty': contribution.penalty, 'is_late': contribution.is_late}, status=201)


class RoundApproveView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        round_obj = get_object_or_404(
            Round.objects.select_for_update().select_related('circle', 'recipient'), pk=pk
        )
        if request.user.pk != round_obj.circle.admin_id:
            return Response({'detail': 'Only the circle admin can approve rounds.'}, status=403)
        if round_obj.status != Round.Status.PENDING_APPROVAL:
            return Response({'detail': 'This round is not pending approval.'}, status=400)

        total_paid = sum(
            contribution.amount_paid or 0
            for contribution in round_obj.contributions.all()
        )
        round_obj.final_payout_amount = (total_paid * 99) // 100
        round_obj.status = Round.Status.CLOSED
        round_obj.approved_at = timezone.now()
        round_obj.save(update_fields=['final_payout_amount', 'status', 'approved_at'])

        recipient = round_obj.recipient
        recipient.paid_out = True
        recipient.save(update_fields=['paid_out'])

        next_recipient = Membership.objects.filter(
            circle=round_obj.circle, paid_out=False
        ).order_by('position').first()
        if next_recipient is not None:
            Round.objects.create(
                circle=round_obj.circle,
                round_number=round_obj.round_number + 1,
                recipient=next_recipient,
                deadline=timezone.now() + timedelta(days=3),
            )

        return Response({
            'id': round_obj.id,
            'status': round_obj.status,
            'final_payout_amount': round_obj.final_payout_amount,
            'approved_at': round_obj.approved_at,
        })
