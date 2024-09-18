from django.urls import path
from .views import UserEnrollmentView, BorrowBookView


urlpatterns = [
    path('users/enroll/', UserEnrollmentView.as_view(), name='user-enroll'),
    path('books/borrow/<int:book_id>', BorrowBookView.as_view(), name='borrow_book'),
]