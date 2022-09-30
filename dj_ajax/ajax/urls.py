# ajax/urls.py
from django.urls import path
from .views import home, SignUpView, validate_username

urlpatterns = [
    path('', home, name='home'),
    path('signup', SignUpView.as_view(), name='signup'),
    path('validate_username', validate_username, name='validate_username')
]


