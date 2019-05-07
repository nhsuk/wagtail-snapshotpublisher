from modelcluster.fields import ParentalKey

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.db.utils import ProgrammingError
from django.dispatch import receiver
from django.forms.models import model_to_dict

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from wagtail.api import APIField
from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.snippets.models import register_snippet

from wagtailsnapshotpublisher.models import PageWithRelease, ModelWithRelease

from wagtail.api import APIField


@register_setting
class SiteSettings(BaseSetting):
    title = models.CharField(max_length=255)


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

    release_config = {
        'can_publish_to_release': True,
        'can_publish_to_live_release': True,
    }

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
        }],
    }

    @property
    def site_code(self):
        return SiteSettings.objects.get(site=self.get_site()).title


# TestPage.release_config['can_publish_to_release'] = True
# TestPage.release_config['can_publish_to_live_release'] = True


class TestModel(ModelWithRelease):
    name1 = models.CharField(max_length=255)
    name2 = models.CharField(max_length=255)

    release_config = {
        'can_publish_to_release': True,
        'can_publish_to_live_release': True,
    }

    panels = ModelWithRelease.panels + [
        FieldPanel('name1'),
        FieldPanel('name2'),
    ]

    structure_to_store = {
        'fields': ['name1', 'name2'],
        'related_fields': ['content_release'],
        'extra': [
            {
                'name': 'redirects',
                'function': 'get_redirections',
            },
        ],
    }

    def get_key(self):
        return 'test_model'

    def __str__(self):
        return '{} - {}'.format(self.name1, self.name2)

    def get_redirections(self):
        redirects = Redirect.objects.all()

        redirect_objects = []

        for redirect in redirects:
            redirect_object = model_to_dict(redirect)
            del(redirect_object['id'])
            del(redirect_object['site'])
            if redirect_object['redirect_page']:
                redirect_object['redirect_link'] = Page.objects.get(id=4).url
                del(redirect_object['redirect_page'])
            else:
                del(redirect_object['redirect_page'])
            redirect_objects.append(redirect_object)
        
        return redirect_objects

# TestPage.release_config['can_publish_to_release'] = False
# TestPage.release_config['can_publish_to_live_release'] = False


@receiver(post_save, sender=SiteSettings)
@receiver(post_delete, sender=SiteSettings)
def update_site_code_for_content_release(sender, instance, **kwargs):
    from django import forms
    from wagtail.admin.edit_handlers import FieldPanel
    from wagtailsnapshotpublisher.models import WSSPContentRelease, ModelWithRelease

    site_settings = SiteSettings.objects.exclude(title='').values_list('title', 'title')

    site_code_widget = forms.Select(
        choices=tuple([('', '---------')] + list(site_settings)),
    )

    WSSPContentRelease.get_panel_field('site_code').widget = site_code_widget
    ModelWithRelease.get_panel_field('site_code').widget = site_code_widget


try:
    update_site_code_for_content_release(SiteSettings, None)
except ProgrammingError:
    pass
