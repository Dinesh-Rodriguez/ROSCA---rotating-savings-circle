from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Circle, Membership
from .serializers import CircleSerializer, LoginSerializer, MembershipSerializer, RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(**serializer.validated_data)
        if user is None:
            return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

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
        return Response(MembershipSerializer(membership).data, status=201)

class CircleDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        circle = get_object_or_404(Circle.objects.prefetch_related('memberships__user'), pk=pk)
        return Response(CircleSerializer(circle).data)
