from django.urls import path
from .views import home, SignUpView, validate_username, contact_form, ContactFormView

urlpatterns = [
    path('', home, name='home'),
    path('signup', SignUpView.as_view(), name='signup'),
    path('validate_username', validate_username, name='validate_username'),
    path('contact-form/', contact_form, name='contact_form'),
   # path('contact-form/', ContactFormView.as_view(), name='contact_form'),
]