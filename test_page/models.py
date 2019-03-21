from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.api import APIField
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.models import Page
from wagtail.snippets.models import register_snippet

from wagtailsnapshotpublisher.models import PageWithRelease, ModelWithRelease


class TestPage(PageWithRelease):
    content_panels = Page.content_panels + [
        FieldPanel('content_release'),
    ]

    fields_to_store = ['title']


class TestModel(ModelWithRelease):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
        FieldPanel('content_release'),
    ]

    fields_to_store = ['name']

    def get_key(self):
        return 'test_model'

    def __str__(self):
        return self.name

