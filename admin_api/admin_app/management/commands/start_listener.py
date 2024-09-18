from django.core.management.base import BaseCommand
from admin_app.consumers import consume_borrow_events

class Command(BaseCommand):
    help = 'Starts the RabbitMQ listener'

    def handle(self, *args, **kwargs):
        consume_borrow_events()
