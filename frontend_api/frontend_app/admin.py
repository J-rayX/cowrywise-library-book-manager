# admin.py
from django.contrib import admin

from .models import UserBook


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = (
        "book_id",
        "title",
        "author",
        "publisher",
        "category",
        "available",
        "added_at",
        "return_date",
    )
