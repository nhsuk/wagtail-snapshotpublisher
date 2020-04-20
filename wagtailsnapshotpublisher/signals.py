from django import dispatch
from django.dispatch import receiver
from django.conf import settings

from azure.storage.queue import QueueService

content_was_published = dispatch.Signal(providing_args=["site_id", "release_id", "title", "content", "page"])
