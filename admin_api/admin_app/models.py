from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    available = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["title", "author"], name="unique_book")
        ]


class AdminUser(models.Model):
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class AdminBorrowing(models.Model):
    user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    book_id = models.IntegerField()  # From Admin API
    borrowed_date = models.DateTimeField(auto_now_add=True)
    borrow_days = models.IntegerField()
    return_date = models.DateTimeField()

    def __str__(self):
        return f"{self.user} borrowed book with ID {self.book_id}"
