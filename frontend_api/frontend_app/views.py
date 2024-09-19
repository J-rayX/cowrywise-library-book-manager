
from rest_framework.views import APIView

from rest_framework import status
from django.core.exceptions import ValidationError
from .models import User

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
            try:
                message = {
                    'email': user.email,
                    'firstname': user.firstname,
                    'lastname': user.lastname,
                }

                self.send_user_enrolled_message(message)
            except Exception as e:
                return JsonResponse({
                    'error': 'Failed to notify admin_api about user enrollment',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return JsonResponse(
                {"message": f"New user, {user.firstname} {user.lastname} enrolled! 🔥"},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def send_user_enrolled_message(self, message):
        """ Sends user enrolled message to RabbitMQ """
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='user_enrolled', durable=False)

        channel.basic_publish(
            exchange='',
            routing_key='user_enrolled',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        connection.close()



class BorrowBookView(APIView):
    def post(self, request, book_id):
        user_email = request.data.get('email')
        # book_id = request.data.get('book_id')
        borrow_days = request.data.get('borrow_days')
        
        if not user_email or not borrow_days:
            return JsonResponse({'error': 'The [user_email and borrow_days] fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            borrow_days = int(borrow_days) 
        except ValueError:
            return JsonResponse({'error': 'borrow_days value must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

        
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
        try:
            borrowing = Borrowing.objects.create(
                user=user,
                book_id=book_id,
                borrow_days=borrow_days,
                return_date=return_date
            )
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while borrowing the book.', 'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # update local UserBook model
        book.available = False
        book.return_date = return_date
        book.save()
        
        # send message to rabbitmq
        try:
            message = {
                'book_id': book_id,
                'available':  book.available,
                'return_date': return_date.isoformat(),
                'borrow_days': borrow_days,
                'borrowed_by': user_email
            }
            self.send_borrow_message_to_queue(message)
            return JsonResponse({'message': 'Book borrowed successfully', 'borrowing_id': borrowing.id },
                                status=status.HTTP_201_CREATED)

        except Exception as e:
            return JsonResponse({
                'error': 'Failed to notify the admin about borrowing', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return JsonResponse({
            'message': 'Book borrowed successfully',
            'borrowing_id': borrowing.id
        }, status=status.HTTP_201_CREATED)

    def send_borrow_message_to_queue(self, message):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='book_borrowed', durable=False)

        channel.basic_publish(
            exchange='',
            routing_key='book_borrowed',
            body=json.dumps(message),
            properties=pika.BasicProperties(content_type='application/json')
        )
        connection.close()
        print(f"Message sent to book_borrowed queue")

        

class AvailableBooksView(APIView):
    def get(self, request):
        try:
            publisher = request.GET.get('publisher')
            category = request.GET.get('category')
          
            available_books = UserBook.objects.filter(available=True)
            if publisher:
                available_books = available_books.filter(publisher=publisher)
            if category:
                available_books = available_books.filter(category=category)
            
            books_list = [
                {
                    'book_id': book.book_id,
                    'title': book.title,
                    'author': book.author,
                    'publisher': book.publisher,
                    'category': book.category,
                }
                for book in available_books
            ]
            if not books_list:
                return JsonResponse({'message': 'No available books found'}, status=status.HTTP_404_NOT_FOUND)
            return JsonResponse({'books': books_list}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while fetching books. ', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetBookByIdView(APIView):
    def get(self, request, book_id):
        try:
            book = UserBook.objects.get(book_id=book_id)
            book_data = {
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'publisher': book.publisher,
                'category': book.category,
                'available': book.available,
                'added_at': book.added_at,
                'return_date': book.return_date
            }
            return JsonResponse(book_data, status=status.HTTP_200_OK)
        except UserBook.DoesNotExist:
            return JsonResponse({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)



class FilterAllBooksView(APIView):
    def get(self, request):
        publisher = request.GET.get('publisher', None) 
        category = request.GET.get('category', None)   

        try: 

            books = UserBook.objects.all()
            if publisher:
                books = books.filter(publisher__icontains=publisher)
            if category:
                books = books.filter(category__icontains=category)

            books_list = [
                {
                    'book_id': book.book_id,
                    'title': book.title,
                    'author': book.author,
                    'publisher': book.publisher,
                    'category': book.category,
                    'available': book.available,
                    'return_date': book.return_date
                }
                for book in books
            ]

            if not books_list:
                return JsonResponse({'message': 'No books found with the provided filters'}, status=status.HTTP_404_NOT_FOUND)
            
            return JsonResponse({'books': books_list}, status=status.HTTP_200_OK)
        
        # except UserBook.DoesNotExist:
        #     return JsonResponse({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({'error': 'Something went wrong', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

