# from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from .models import Book



class AddBookView(APIView):
    def post(self, request):
        # Extract data from request
        # book_id = request.data.get('book_id')
        title = request.data.get('title')
        author = request.data.get('author')
        publisher = request.data.get('publisher')
        category = request.data.get('category')

        #  Required field validation
        if not all([title, author, publisher, category]):
            return Response({
                'error': 'The [title, author, publisher, category] fields are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(title) > 200:
            return Response({
                'error': 'Title must not be above 200 character.'
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
            if 'unique constraint' in str(e).lower():
                return Response({
                    'error': 'A book with this title and author already exists.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'An error occurred while creating the book.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
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

class RemoveBookView(APIView):
    def delete(self, request, book_id):
        try:
            book = Book.objects.get(book_id=book_id)
            book.delete()
            return JsonResponse({'message': 'Book removed successfully!'}, status=status.HTTP_200_OK)
        except Book.DoesNotExist:
            return JsonResponse({'error': 'Book not found'}, status=404)

