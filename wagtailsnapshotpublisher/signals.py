import logging
​
from django import dispatch
from django.dispatch import receiver
​
logger = logging.getLogger('django')
​
content_was_published = dispatch.Signal(providing_args=["site_id", "release_id", "title", "content"])
​
@receiver(content_was_published)
def handle_content_was_published(sender, site_id, release_id, title, content, **kwargs):
    logger.info('Content was published %s %s %s', site_id, release_id, title)