
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from frontend_app.models import User, UserBook, Borrowing
from unittest.mock import patch
from django.utils import timezone
from dateutil.parser import isoparse

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pika


class UserEnrollmentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user-enroll')

    def test_enroll_new_user_success(self):
        payload = {
            'email': 'jkaylight@gmail.com',
            'firstname': 'Jekayin-Oluwa',
            'lastname': 'Olabemiwo'
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, payload['email'])

    def test_enroll_user_with_existing_email(self):
        existing_user = User.objects.create(
            email='jkaylight@gmail.com',
            firstname='Jekayin-Oluwa',
            lastname='Olabemiwo'
        )
        payload = {
            'email':'jkaylight@gmail.com',
            'firstname': 'Jekayin-Oluwa',
            'lastname': 'Ola'
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_json = response.json()
        self.assertEqual(response_json['error'], 'A user with this email already exists.')
        self.assertEqual(User.objects.count(), 1)


class BorrowBookViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('borrow-book', args=[1]) 
        self.user = User.objects.create(email='testuser@example.com', firstname='Test', lastname='User')
        self.book = UserBook.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=True,
            return_date=None
        )
    
    @patch('frontend_app.views.BorrowBookView.send_borrow_message_to_queue') 
    def test_borrow_book_successfully(self, mock_queue):
        mock_queue.return_value = None 
        
        payload = {
            'email': self.user.email,
            'borrow_days': 7
        }
        
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        self.assertFalse(UserBook.objects.get(book_id=1).available)
        mock_queue.assert_called_once() 
    
    def test_borrow_book_user_not_found(self):
        payload = {
            'email': 'nonexistentuser@example.com',
            'borrow_days': 7
        }
        
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'User not found')
    
    def test_borrow_book_not_found(self):
        url = reverse('borrow-book', args=[29])
        payload = {
            'email': self.user.email,
            'borrow_days': 7
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'Book not found')
    
    def test_borrow_book_already_borrowed(self):
        self.book.available = False
        self.book.save()
        
        payload = {
            'email': self.user.email,
            'borrow_days': 7
        }
        
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'Book is not available for borrowing')
    
    @patch('frontend_app.views.BorrowBookView.send_borrow_message_to_queue') 
    def test_borrow_book_queue_error(self, mock_queue):
        mock_queue.side_effect = Exception('Queue error')
        
        payload = {
            'email': self.user.email,
            'borrow_days': 7
        }
        
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()['error'], 'Failed to notify the admin about borrowing')


class AvailableBooksViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('available-books') 

        self.book1 = UserBook.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=True
        )
        self.book2 = UserBook.objects.create(
            book_id=2,
            title='Expert Secrets',
            author='Russell Brunson',
            publisher='Morgan-James Publishing',
            category='Marketing',
            available=True
        )
        # self.book3 = UserBook.objects.create(
        #     book_id=3,
        #     title='The Design of Everyday Things',
        #     author='Donald A. Norman',
        #     publisher='MIT Press',
        #     category='Design',
        #     available=False
        # )

    def test_get_available_books(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['books']), 2)
        self.assertEqual(response.json()['books'][0]['book_id'], self.book1.book_id)
        self.assertEqual(response.json()['books'][1]['book_id'], self.book2.book_id)

    def test_get_available_books_with_publisher_filter(self):
        response = self.client.get(self.url, {'publisher': 'Clear-Coast'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['books']), 1)
        self.assertEqual(response.json()['books'][0]['book_id'], self.book1.book_id)

    def test_get_available_books_with_publisher_and_category_filter(self):
        response = self.client.get(self.url, {'publisher': 'Clear-Coast', 'category': 'Writing'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['books']), 1)
        self.assertEqual(response.json()['books'][0]['book_id'], self.book1.book_id)


class GetBookByIdViewTests(APITestCase):
    def setUp(self):
        self.book = UserBook.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=True,
            added_at=timezone.now(),  
            return_date=None
        )
        self.url = reverse('get-book', args=[self.book.book_id])
        self.client = APIClient()

    def test_get_book_by_id_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        response_added_at = isoparse(response_data['added_at']).replace(microsecond=0)
        true_added_at = self.book.added_at.replace(microsecond=0)

        self.assertEqual(response_data['book_id'], self.book.book_id)
        self.assertEqual(response_data['title'], self.book.title)
        self.assertEqual(response_data['author'], self.book.author)
        self.assertEqual(response_data['publisher'], self.book.publisher)
        self.assertEqual(response_data['category'], self.book.category)
        self.assertEqual(response_data['available'], self.book.available)
        self.assertEqual(response_added_at, true_added_at)
        self.assertEqual(response_data['return_date'], self.book.return_date)

    def test_get_book_by_id_not_found(self):
        response = self.client.get(reverse('get-book', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'Book not found')

    def test_get_book_by_id_invalid_id(self):
        with self.assertRaises(ValueError):
            # response = self.client.get(reverse('get-book', args=['invalid']))
            # can't pass string directly since urlpattern only accepts integer
            url = reverse('get-book', args=[1])
            response = self.client.get(f'/books/invalid/')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.json()['error'], 'Book not found')


class FilterAllBooksViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.book1 = UserBook.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=True,
            added_at=timezone.now(),
            return_date=None
        )
        
        self.book2 = UserBook.objects.create(
            book_id=2,
            title='Expert Secrets',
            author='Russell Brunson',
            publisher='Morgan-James Publishing',
            category='Marketing',
            available=True,
            added_at=timezone.now(),
            return_date=None
        )
        
        self.book3 = UserBook.objects.create(
            book_id=3,
            title='The Design of Everyday Things',
            author='Donald A. Norman',
            publisher='MIT Press',
            category='Design',
            available=False,
            added_at=timezone.now(),
            return_date=None
        )

    def test_filter_books_by_category(self):
        url = reverse('filter-books') + '?category=Marketing'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['books']), 1)
        self.assertEqual(response_data['books'][0]['title'], self.book2.title)

    def test_filter_books_by_publisher_and_category(self):
        url = reverse('filter-books') + '?publisher=MIT PRess&category=Design'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['books']), 1)
        self.assertEqual(response_data['books'][0]['title'], self.book3.title)

    def test_filter_books_no_results(self):
        url = reverse('filter-books') + '?publisher=Noone'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['message'], 'No books found with the provided filters')

    def test_filter_books_invalid_parameters(self):
        url = reverse('filter-books') + '?publisher=Clear-Coast&invalid_param=some_value'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(any(book['publisher'] == 'Clear-Coast' for book in response_data['books']))

    def test_filter_books_empty_filters(self):
        url = reverse('filter-books')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['books']), 3)  

    def test_filter_books_exception_handling(self):
        with self.assertRaises(Exception):
            url = reverse('filter-books') + '?publisher='
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Something went wrong', response.json()['error'])