from django.urls import path
from .views import UserEnrollmentView


urlpatterns = [
    path('users/enroll/', UserEnrollmentView.as_view(), name='user-enroll'),
]