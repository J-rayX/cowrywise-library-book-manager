import pika
import json
from .models import Book
from django.utils.dateparse import parse_datetime


def consume_borrow_events():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='book_borrowed')

    def callback(ch, method, properties, body):
        print(f"Received borrow event: {body}")
        data = json.loads(body)
        book_id = data['book_id']
        available = data['available']
        return_date_str = data['return_date']

        return_date = parse_datetime(return_date_str)

        try:
            book = Book.objects.get(book_id=book_id)
            book.available = available
            book.return_date = return_date
            book.save()
            print(f"Updated book {book.title} as unavailable and {book.return_date} return_date.")
        except Book.DoesNotExist:
            print(f"Book with ID {book_id} does not exist")

    channel.basic_consume(queue='book_borrowed', on_message_callback=callback, auto_ack=True)
    print('Waiting for borrow events...')
    channel.start_consuming()


