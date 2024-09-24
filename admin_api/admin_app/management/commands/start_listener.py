from threading import Thread

from admin_app.consumers import consume_borrowed, consume_user_enrolled
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Kickstarts the RabbitMQ listener"

    def handle(self, *args, **kwargs):
        Thread(target=consume_borrowed).start()
        Thread(target=consume_user_enrolled).start()
