from django.urls import path

from .views import CircleCreateView, CircleDetailView, CircleJoinView, LoginView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]
