from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.db import IntegrityError
from admin_app.models import Book, AdminUser, AdminBorrowing
import json
import pika
from unittest.mock import patch



class AddBookViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('add-book')
    
        self.book1 = Book.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=True
        )
        self.book2 = Book.objects.create(
            book_id=2,
            title='Expert Secrets',
            author='Russell Brunson',
            publisher='Morgan-James Publishing',
            category='Marketing',
            available=True
        )

        self.valid_data = {
            'title':'The Design of Everyday Things',
            'author':'Donald A. Norman',
            'publisher':'MIT Press',
            'category':'Design',
        }
    
    @patch('admin_app.views.pika.BlockingConnection') 
    def test_add_book_success(self, mock_pika):
        mock_channel = mock_pika.return_value.channel.return_value
        mock_channel.queue_declare.return_value = None
        mock_channel.basic_publish.return_value = None

        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'New book added! 🔥')
        self.assertIn('book_id', response_data['book'])
        self.assertEqual(response_data['book']['title'], self.valid_data['title'])
        self.assertEqual(response_data['book']['author'], self.valid_data['author'])
        self.assertEqual(response_data['book']['publisher'], self.valid_data['publisher'])
        self.assertEqual(response_data['book']['category'], self.valid_data['category'])

        mock_channel.basic_publish.assert_called_once()

    def test_add_book_missing_fields(self):
        response = self.client.post(self.url, {'author': 'Author', 'publisher': 'Publisher', 'category': 'Category'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'The [title, author, publisher, category] fields are required.')

        response = self.client.post(self.url, {'title': 'Title', 'publisher': 'Publisher', 'category': 'Category'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'The [title, author, publisher, category] fields are required.')

    def test_add_book_title_length_exceed(self):
        long_title = 'A' * 201
        data = {**self.valid_data, 'title': long_title}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'Title must not be above 200 character.')

    def test_add_book_duplicate(self):
        duplicate_data = {
            'title': 'Determination Unshakable',
            'author': 'Goodluck Jonathan',
            'publisher': 'Clear-Coast',
            'category': 'Writing'
        }
        response = self.client.post(self.url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'A Book with this title and author already exists.')


class RemoveBookViewTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('remove-book', args=[1])

       
        self.book = Book.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=True
        )

    @patch('admin_app.views.pika.BlockingConnection')
    def test_remove_book_success(self, mock_pika):
        mock_channel = mock_pika.return_value.channel.return_value
        mock_channel.queue_declare.return_value = None
        mock_channel.basic_publish.return_value = None

        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['message'], 'Book removed successfully!')

        # check if the book was removed from the dB
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(book_id=1)

        mock_channel.basic_publish.assert_called_once()

    def test_remove_book_not_found(self):
        url = reverse('remove-book', args=[87])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'Book not found')



class UnavailableBooksViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('unavailable-books')

        self.book1 = Book.objects.create(
            book_id=1,
            title='Determination Unshakable',
            author='Goodluck Jonathan',
            publisher='Clear-Coast',
            category='Writing',
            available=False,
            return_date='2024-10-01'
        )
        self.book2 = Book.objects.create(
            book_id=2,
            title='Expert Secrets',
            author='Russell Brunson',
            publisher='Morgan-James Publishing',
            category='Marketing',
            available=False,
            return_date='2024-10-15'
        )
        self.book3 = Book.objects.create(
            book_id=3,
            title='The Design of Everyday Things',
            author='Donald A. Norman',
            publisher='MIT Press',
            category='Design',
            available=True,
            return_date=None
        )

    def test_get_unavailable_books_success(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        books = response_data['books']
        self.assertEqual(len(books), 2)
        self.assertIn('book_id', books[0])
        self.assertIn('title', books[0])
        self.assertIn('author', books[0])
        self.assertIn('publisher', books[0])
        self.assertIn('category', books[0])
        self.assertIn('available_date', books[0])

        self.assertEqual(books[0]['book_id'], 1)
        self.assertEqual(books[1]['book_id'], 2)

    @patch('admin_app.views.Book.objects.filter')
    def test_get_unavailable_books_exception(self, mock_filter):
        # mock an exception in the DB query
        mock_filter.side_effect = Exception('Database query failed')
        
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()['error'], 'An error occurred while fetching unavailable books.')


class AdminUserListViewTests(APITestCase):

    def setUp(self):
        self.url = reverse('users-list')
        self.user1 = AdminUser.objects.create(
            email='jkaylight@gmail.com',
            firstname='JekayinOluwa',
            lastname='Olabemiwo',
            created_at='2024-01-01T12:00:00Z'
        )
        self.user2 = AdminUser.objects.create(
            email='jkaylight01@gmail.com',
            firstname='Ogbeni',
            lastname='Jk',
            created_at='2024-03-01T12:00:00Z'
        )
        self.user3 = AdminUser.objects.create(
            email='jkaylight02@gmail.com',
            firstname='Mister',
            lastname='JkO',
            created_at='2024-03-01T12:00:00Z'
        )

    def test_get_admin_user_list_success(self):
        response = self.client.get(self.url, format='json')
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response_data)
        self.assertEqual(len(response_data['users']), 3)

        users = response_data['users']
        user1 = next(user for user in users if user['email'] == 'jkaylight@gmail.com')
        self.assertEqual(user1['firstname'], 'JekayinOluwa')
        self.assertEqual(user1['lastname'], 'Olabemiwo')

        user2 = next(user for user in users if user['email'] == 'jkaylight01@gmail.com')
        self.assertEqual(user2['firstname'], 'Ogbeni')
        self.assertEqual(user2['lastname'], 'Jk')

        user3 = next(user for user in users if user['email'] == 'jkaylight02@gmail.com')
        self.assertEqual(user3['firstname'], 'Mister')
        self.assertEqual(user3['lastname'], 'JkO')

    def test_get_admin_user_list_no_users(self):
        AdminUser.objects.all().delete()

        response = self.client.get(self.url, format='json')
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response_data['error'], 'No users found')

    def test_get_admin_user_list_exception(self):
        with patch('admin_app.views.AdminUser.objects.all') as mock_all:
            mock_all.side_effect = Exception('Database query failed')

            response = self.client.get(self.url, format='json')
            response_data = response.json()

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error'], 'An error occurred while fetching users')
            self.assertIn('detail', response_data)



class UserBorrowingListViewTests(APITestCase):

    def setUp(self):
        self.url = reverse('users-borrows-list')
        
        self.user1 = AdminUser.objects.create(
            email='jkaylight@gmail.com',
            firstname='JekayinOluwa',
            lastname='Olabemiwo',
            created_at='2024-01-01T12:00:00Z'
        )
        self.user2 = AdminUser.objects.create(
            email='jkaylight01@gmail.com',
            firstname='Ogbeni',
            lastname='Jk',
            created_at='2024-03-01T12:00:00Z'
        )

        self.borrowing1 = AdminBorrowing.objects.create(
            user=self.user1,
            book_id=1,
            borrow_days=7,
            return_date='2024-09-30'
        )
        self.borrowing2 = AdminBorrowing.objects.create(
            user=self.user2,
            book_id=2,
            borrow_days=14,
            return_date='2024-10-15'
        )

    @patch('admin_app.views.AdminUser.objects.all')
    @patch('admin_app.views.AdminBorrowing.objects.filter')
    def test_get_user_borrowing_list_success(self, mock_borrowings, mock_users):
        mock_users.return_value = [self.user1, self.user2]
        mock_borrowings.side_effect = lambda user: [self.borrowing1] if user == self.user1 else [self.borrowing2] if user == self.user2 else []

        response = self.client.get(self.url, format='json')
        print("Response Data:", response.content.decode())
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response_data)

        user1_data = next((user for user in response_data['users'] if user['user_email'] == 'jkaylight@gmail.com'), None)
        self.assertIsNotNone(user1_data, "User with email 'jkaylight@gmail.com' not found in response")
        self.assertEqual(user1_data['firstname'], 'JekayinOluwa')
        self.assertEqual(user1_data['lastname'], 'Olabemiwo')
        self.assertEqual(len(user1_data['borrowed_books']), 1)
        
        borrowed_books1 = {book['book_id'] for book in user1_data['borrowed_books']}
        self.assertIn(1, borrowed_books1)

        user2_data = next((user for user in response_data['users'] if user['user_email'] == 'jkaylight01@gmail.com'), None)
        self.assertIsNotNone(user2_data, "User with email 'jkaylight01@gmail.com' not found in response")
        self.assertEqual(user2_data['firstname'], 'Ogbeni')
        self.assertEqual(user2_data['lastname'], 'Jk')
        self.assertEqual(len(user2_data['borrowed_books']), 1)
        
        borrowed_books2 = {book['book_id'] for book in user2_data['borrowed_books']}
        self.assertIn(2, borrowed_books2)
