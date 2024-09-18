# from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from .models import Book
import pika
import json
from django.conf import settings


RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_QUEUE = 'book_added'
# RABBITMQ_USER = 'jkaylight'
# RABBITMQ_PASSWORD = 'password'



class AddBookView(APIView):
    def post(self, request):
        # book_id = request.data.get('book_id')
        title = request.data.get('title')
        author = request.data.get('author')
        publisher = request.data.get('publisher')
        category = request.data.get('category')

        #  Required field validation
        if not all([title, author, publisher, category]):
            return JsonResponse({
                'error': 'The [title, author, publisher, category] fields are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(title) > 200:
            return JsonResponse({
                'error': 'Title must not be above 200 character.'
            }, status=status.HTTP_400_BAD_REQUEST)
        # chceking if book already
        if Book.objects.filter(title=title, author=author).exists():
            return JsonResponse({
                'error': 'A Book with this title and author already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # DB seeding
        try:
            book = Book.objects.create(
                title=title,
                author=author,
                publisher=publisher,
                category=category,
            )
        except IntegrityError as e:
            return JsonResponse({
                'error': 'An error occurred while creating the book.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # put message on queue
        self.send_book_create_message_to_queue({
            'book_id': book.book_id,
            'title': book.title,
            'author': book.author,
            'publisher': book.publisher,
            'category': book.category,
            'available': book.available,
            'added_at': book.added_at.isoformat()
        })

        return JsonResponse({
            'message': 'New book added! 🔥',
            'book': {
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'publisher': book.publisher,
                'category': book.category,
                'available': book.available,
                'added_at': book.added_at
            }
        }, status=status.HTTP_201_CREATED)
    

    def send_book_create_message_to_queue(self, message):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # connection = pika.BlockingConnection(pika.ConnectionParameters(
        #     host=settings.RABBITMQ_HOST, port=settings.RABBITMQ_PORT
        # ))
        channel = connection.channel()
        channel.queue_declare(queue='book_added', durable=False)

        channel.basic_publish(
            exchange='',
            routing_key='book_added',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  
            )
        )
        connection.close()
        


class RemoveBookView(APIView):
    def delete(self, request, book_id):
        try:
            book = Book.objects.get(book_id=book_id)
            book.delete()
            try:
                self.send_delete_book_message(book_id)
            except Exception as e:
                print(f"Error sending book_removed message: {str(e)}")
                return JsonResponse(
                    {'message': 'Book removed, but failed to notify external system.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return JsonResponse({'message': 'Book removed successfully!'}, status=status.HTTP_200_OK)
        except Book.DoesNotExist:
            return JsonResponse({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def send_delete_book_message(self, book_id):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='book_removed', durable=False)

            message = json.dumps({'book_id': book_id})

            channel.basic_publish(exchange='',
                                routing_key='book_removed',
                                body=message)
            print(f"Sent delete event for book ID: {book_id}")
        except Exception as e:
            print(f"Unable to reach RabbitMQ: {str(e)}")
            return JsonResponse({'error': 'Trouble attending to request'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if connection:
                connection.close()



class UnavailableBooksView(APIView):
    def get(self, request):
        unavailable_books = Book.objects.filter(available=False)
        books_list = [
            {
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'publisher': book.publisher,
                'category': book.category,
                'available_date': book.return_date
            }
            for book in unavailable_books
        ]
        return JsonResponse({'books': books_list}, status=status.HTTP_200_OK)
