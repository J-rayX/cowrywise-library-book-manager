from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import User



class UserEnrollmentView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email')
        firstname = data.get('firstname')
        lastname = data.get('lastname')

        # Required field validation
        if not all([email, firstname, lastname]):
            return Response(
                {"error": "The [email, firstname, lastname] fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create(email=email, firstname=firstname, lastname=lastname)
            return Response(
                {"message": f"New user, {user.firstname} {user.lastname} enrolled! 🔥"},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


