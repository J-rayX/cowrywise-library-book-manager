from django.urls import path
from .views import UserEnrollmentView, BorrowBookView, AvailableBooksView, GetBookByIdView, FilterAllBooksView


urlpatterns = [
    path('users/enroll/', UserEnrollmentView.as_view(), name='user-enroll'),
    path('books/<int:book_id>/', GetBookByIdView.as_view(), name='get-book'),
    path('books/borrow/<int:book_id>', BorrowBookView.as_view(), name='borrow-book'),

    path('books/available/', AvailableBooksView.as_view(), name='available-books'),
    path('books/filter/', FilterAllBooksView.as_view(), name='filter-books'),

]