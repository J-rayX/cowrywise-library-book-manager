from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import User

from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import json
import pika
from django.http import JsonResponse

from .models import Borrowing, User, UserBook
from django.conf import settings


RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_QUEUE = 'book_borrowed'

class UserEnrollmentView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email')
        firstname = data.get('firstname')
        lastname = data.get('lastname')

        # Required field validation
        if not all([email, firstname, lastname]):
            return JsonResponse(
                {"error": "The [email, firstname, lastname] fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create(email=email, firstname=firstname, lastname=lastname)
            return JsonResponse(
                {"message": f"New user, {user.firstname} {user.lastname} enrolled! 🔥"},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



class BorrowBookView(APIView):
    def post(self, request, book_id):
        user_email = request.data.get('email')
        # book_id = request.data.get('book_id')
        borrow_days = int(request.data.get('borrow_days'))
        
        if not user_email or not borrow_days:
            return JsonResponse({'error': 'The [user_email and borrow_days] fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=user_email)
            book = UserBook.objects.get(book_id=book_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserBook.DoesNotExist:
            return JsonResponse({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        if not book.available:
            return JsonResponse({'error': 'Book is not available for borrowing'}, status=status.HTTP_400_BAD_REQUEST)
        
        # create new Borrowing instance
        return_date = timezone.now() + timedelta(days=int(borrow_days))
        borrowing = Borrowing.objects.create(
            user=user,
            book_id=book_id,
            borrow_days=borrow_days,
            return_date=return_date
        )
        
        # update local UserBook model
        book.available = False
        book.return_date = return_date
        book.save()
        
        # send message to rabbitmq
        try:
            self.send_borrow_event_to_queue(book_id, False, return_date)
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to notify the admin_api about borrowing', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return JsonResponse({'message': 'Book borrowed successfully', 'borrowing_id': borrowing.id}, status=status.HTTP_201_CREATED)


    def send_borrow_event_to_queue(self, book_id, available, return_date):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            # connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.RABBITMQ_HOST,port=settings.RABBITMQ_PORT))
            channel = connection.channel()
            channel.queue_declare(queue='book_borrowed')

            # put message on 'book_borrowed' queue
            message = json.dumps({
                'book_id': book_id,
                'available': available,
                'return_date': return_date.isoformat() if return_date else None
            })

            channel.basic_publish(exchange='', routing_key='book_borrowed', body=message)
            print(f"Sent borrow event for book ID: {book_id}, Return Date: {return_date}")
        except Exception as e:
            print(f"Unable to reach rabbitmq: {str(e)}")
        finally:
            if connection:
                connection.close()
