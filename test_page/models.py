from modelcluster.fields import ParentalKey

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.db.utils import ProgrammingError
from django.dispatch import receiver

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from wagtail.api import APIField
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.snippets.models import register_snippet

from wagtailsnapshotpublisher.models import PageWithRelease, ModelWithRelease

from wagtail.api import APIField

class SimpleRichText(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    body = blocks.RichTextBlock(required=False)

    fields_to_store = ['title', 'body']



class BlockList(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    body = blocks.StreamBlock([
        ('simple_richtext', SimpleRichText(icon='title')),
    ], null=True)

    fields_to_store = ['title', 'body']


class TestRelatedModel(models.Model):
    test_page = ParentalKey('TestPage', on_delete=models.CASCADE, related_name='test_related_model')
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

    structure_to_store = {
         'fields': ['name'],
    }


class TestPage(PageWithRelease):
    name1 = models.CharField(max_length=255)
    name2 = models.CharField(max_length=255)

    body = StreamField([
        ('simple_richtext', SimpleRichText(icon='title')),
        ('block_list', BlockList()),
    ], null=True)

    content_panels = Page.content_panels + [
        FieldPanel('name1'),
        FieldPanel('name2'),
        StreamFieldPanel('body'),
        InlinePanel('test_related_model', label='Test Related Model', min_num=0, max_num=1),
        FieldPanel('content_release'),
    ]

    structure_to_store = {
        'fields': ['title', 'name1', 'body'],
        'related_fields': ['test_related_model'],
        'children': [{
            'name': 'child1',
            'fields': ['name1'],
            'related_fields': ['test_related_model'],
            'children': [{
                'name': 'child2',
                'fields': ['name2'],
            }]
        }, {
             'name': 'child3',
            'fields': ['name2'],
        }]
    }


class TestModel(ModelWithRelease):
    name1 = models.CharField(max_length=255)
    name2 = models.CharField(max_length=255)

    panels = [
        FieldPanel('name1'),
        FieldPanel('name2'),
        FieldPanel('content_release'),
    ]

    structure_to_store = {
        'fields': ['name1', 'name2'],
    }

    def get_key(self):
        return 'test_model'

    def __str__(self):
        return self.name


@register_setting
class SiteSettings(BaseSetting):
    title = models.CharField(max_length=255)


@receiver(post_save, sender=SiteSettings)
@receiver(post_delete, sender=SiteSettings)
def update_site_code_for_content_release(sender, instance, **kwargs):
    from django import forms
    from wagtail.admin.edit_handlers import FieldPanel
    from wagtailsnapshotpublisher.models import WSSPContentRelease

    site_code_widget = forms.Select(
        choices=tuple(SiteSettings.objects.exclude(title='').values_list('title', 'title')),
    )

    WSSPContentRelease.get_panel_field('site_code').widget = site_code_widget


try:
    update_site_code_for_content_release(SiteSettings, None)
except ProgrammingError:
    pass
