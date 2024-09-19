import pika
import json
from django.http import JsonResponse
import django
import os
from django.utils.dateparse import parse_datetime



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_api.settings")
django.setup()


from .models import UserBook 

def consume_book_added():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # connection = pika.BlockingConnection(pika.ConnectionParameters( host='localhost', port=5672 ))
    channel = connection.channel()   
    channel.queue_declare(queue='book_added')
    
    # callback processes messages
    def callback(ch, method, properties, body):
        message = json.loads(body)
        book_id = message['book_id']
        title = message['title']
        available = message['available']
        author = message['author']
        publisher = message['publisher']
        category = message['category']
        added_at = message['added_at']
        return_date = message.get('return_date', None)

        added_at = parse_datetime(added_at)
        return_date = parse_datetime(return_date) if return_date else None

        print("Received in frontend_api:", message)

        # create book if not in frontend UserBook table
        try:
            if not UserBook.objects.filter(book_id=book_id).exists():
                book = UserBook(
                    book_id=book_id,
                    title=title,
                    author=author,
                    publisher=publisher,
                    category=category,
                    available=available,
                    added_at=added_at,
                    return_date=return_date
                )
                book.save()
                print(f"Saved new book {book.book_id}, {book.title}")
            else:
                print(f"Book {book_id} already exists and was not created.")
        except Exception as e:
            print(f"Error saving book: {str(e)}")

    # configure rabbitmq consumer
    channel.basic_consume(queue='book_added', on_message_callback=callback, auto_ack=True)
    
    print('Waiting for new book addition messages...')
    channel.start_consuming()



def consume_book_removed():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    # channel.queue_declare(queue='book_removed')
    channel.queue_declare(queue='book_removed', durable=False)

    def callback(ch, method, properties, body):
        message = json.loads(body)
        book_id = message.get('book_id')
        if not book_id:
            print("No book ID provided")
            return
        print("Received in frontend_api:", message)

        # delete book if found in frontend UserBook table
        try:
            book = UserBook.objects.get(book_id=book_id)
            book.delete()
            print(f"Deleted book with ID: {book_id}")
        except UserBook.DoesNotExist:
            print(f"Book with ID {book_id} not found")  
        except Exception as e:
            print(f"Error deleting book from UserBook: {str(e)}")
            
    # configure rabbitmq consumer
    channel.basic_consume(queue='book_removed', on_message_callback=callback, auto_ack=True)
    
    print('Waiting for book removal messages...')
    channel.start_consuming()
