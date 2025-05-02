from django.urls import path
from .views import RegisterView, CustomTokenObtainPairView, TokenVerifyView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('signin/', CustomTokenObtainPairView.as_view(), name='signin'),
    path('verify/', TokenVerifyView.as_view(), name='verify_token'),
]
