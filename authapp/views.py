from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer
from django.contrib.auth import authenticate

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class CustomTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        user = None
        if "@" in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(username=username_or_email, password=password)

        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid credentials or inactive account.")

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
        }

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

class TokenVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return Response(
                {"error": "No token provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            user = User.objects.get(id=user_id)
            
            return Response({
                "valid": True,
                "username": user.username,
                "email": user.email,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"valid": False, "error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )