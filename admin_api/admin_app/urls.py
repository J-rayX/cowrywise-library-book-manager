from django.urls import path

from .views import (
    AddBookView,
    AdminUserListView,
    RemoveBookView,
    UnavailableBooksView,
    UserBorrowingListView,
)

urlpatterns = [
    path("books/add/", AddBookView.as_view(), name="add-book"),
    path("books/remove/<int:book_id>", RemoveBookView.as_view(), name="remove-book"),
    path(
        "books/unavailable/", UnavailableBooksView.as_view(), name="unavailable-books"
    ),
    path("users/", AdminUserListView.as_view(), name="users-list"),
    path("users/borrow/", UserBorrowingListView.as_view(), name="users-borrows-list"),
]
