import pika
import json
from .models import Book, AdminUser, AdminBorrowing
from django.utils.dateparse import parse_datetime


def consume_borrowed():
    # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
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
            user = AdminUser.objects.get(email=data['borrowed_by'])
        except AdminUser.DoesNotExist:
            print(f"User with email {data['borrowed_by']} not found in AdminUser")
            return

        try:
            book = Book.objects.get(book_id=book_id)
            book.available = available
            book.return_date = return_date
            book.save()
            print(f"Updated book {book.title} as unavailable and {book.return_date} return_date.")

            AdminBorrowing.objects.create(
                user=user,
                book_id=data['book_id'],
                borrow_days=data['borrow_days'],
                return_date=return_date
            )
            print(f"Borrowing record created for user {user.email}")
        
        except Book.DoesNotExist:
            print(f"Book with ID {book_id} does not exist")

    channel.basic_consume(queue='book_borrowed', on_message_callback=callback, auto_ack=True)
    print('Waiting for book borrow events...')
    channel.start_consuming()



def consume_user_enrolled():
    print("Waiting for user enrollment events...")
    # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='user_enrolled', durable=False)

    def callback(ch, method, properties, body):
        print(f"Received user enrollment event: {body}")
        message = json.loads(body)

        email = message['email']
        firstname = message['firstname']
        lastname = message['lastname']

        try:
            if AdminUser.objects.filter(email=email).exists():
                print(f"User with email {email} already exists.")
            else:
                AdminUser.objects.create(email=email, firstname=firstname, lastname=lastname)
                print(f"New user {firstname} {lastname} added to AdminUser Db.")
        except Exception as e:
            print(f"Error adding user to AdminUser database: {str(e)}")


    # configure rabbitmq consumer
    channel.basic_consume(queue='user_enrolled', on_message_callback=callback, auto_ack=True)

    print('Waiting for user enrollment events...')
    channel.start_consuming()
