import logging

from django import dispatch
from django.dispatch import receiver

logger = logging.getLogger('django')

content_was_published = dispatch.Signal(providing_args=["site_id", "release_id", "title", "content", "page"])

logger.info("IMPORTING WAGTAILSNAPSHOTPUBLISHER SIGNALS")
