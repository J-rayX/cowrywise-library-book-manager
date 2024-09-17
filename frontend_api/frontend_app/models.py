from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_id = models.IntegerField()  # From Admin API
    borrowed_date = models.DateTimeField(auto_now_add=True)
    borrow_days = models.IntegerField()
    return_date = models.DateTimeField()

    def __str__(self):
        return f"{self.user} borrowed book with ID {self.book_id}"

