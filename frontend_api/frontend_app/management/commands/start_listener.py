from django.core.management.base import BaseCommand
from threading import Thread
from frontend_app.consumers import consume_book_added, consume_book_removed

class Command(BaseCommand):
    help = 'Kickstarts the RabbitMQ listener'

    def handle(self, *args, **kwargs):
#         consume_book_added()
#         consume_book_removed()
        Thread(target=consume_book_added).start()
        Thread(target=consume_book_removed).start()
