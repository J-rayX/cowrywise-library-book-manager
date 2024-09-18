import pika
import json
from .models import Book

def consume_borrow_events():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='book_borrowed')

    def callback(ch, method, properties, body):
        print(f"Received borrow event: {body}")
        data = json.loads(body)
        book_id = data['book_id']

        try:
            book = Book.objects.get(book_id=book_id)
            book.available = False
            book.save()
            print(f"Updated book {book.title} as unavailable")
        except Book.DoesNotExist:
            print(f"Book with ID {book_id} does not exist")

    channel.basic_consume(queue='book_borrowed', on_message_callback=callback, auto_ack=True)
    print('Waiting for borrow events...')
    channel.start_consuming()
