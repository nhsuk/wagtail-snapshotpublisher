"""
.. module:: test_page.models
"""

from modelcluster.fields import ParentalKey

from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.db.utils import ProgrammingError
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.template.defaultfilters import slugify

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page

from wagtailsnapshotpublisher.models import PageWithRelease, ModelWithRelease



class SiteSettings(ModelWithRelease):
    """ SiteSettings """
    title = models.CharField(max_length=255)
    slug = models.SlugField(null=True, blank=True)

    site = models.ForeignKey(
        'wagtailcore.Site',
        on_delete=models.CASCADE,
    )

    panels = ModelWithRelease.panels + [
        FieldPanel('title'),
        FieldPanel('slug'),
        FieldPanel('site'),
    ]

    def __str__(self):
        """ __str__ """
        return self.title

    def save(self):
        """ save """
        if not self.slug:
            self.slug = slugify(self.title)
        super(SiteSettings, self).save()


class SimpleRichText(blocks.StructBlock):
    """ SimpleRichText """
    title = blocks.CharBlock(required=True)
    body = blocks.RichTextBlock(required=False)


class BlockList(blocks.StructBlock):
    """ BlockList """
    title = blocks.CharBlock(required=True)
    body = blocks.StreamBlock([
        ('simple_richtext', SimpleRichText(icon='title')),
    ], null=True)


class TestRelatedModel(models.Model):
    """ TestRelatedModel """
    test_page = ParentalKey('TestPage', on_delete=models.CASCADE, related_name='test_related_model')
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

class DynamicTestPageBlock(blocks.PageChooserBlock):
    """ DynamicTestPageBlock """

    def get_api_representation(self, value, context=None):
        """ get_api_representation """
        return {
            'ref': {
                'id': value.id,
                'serializer': 'cover',
                'dynamic': True,
                'app': value.__class__._meta.app_label,
                'class': value.__class__._meta.object_name,
            }
        }


class TestPage(PageWithRelease):
    """ TestPage """
    name1 = models.CharField(max_length=255)
    name2 = models.CharField(max_length=255)

    release_config = {
        'can_publish_to_release': True,
        'can_publish_to_live_release': True,
    }

    body = StreamField([
        ('simple_richtext', SimpleRichText(icon='title')),
        ('block_list', BlockList()),
        ('block_list', BlockList()),
        ('dynamictestpage_block', DynamicTestPageBlock('test_page.TestPage')),
    ], null=True)

    content_panels = Page.content_panels + [
        FieldPanel('name1'),
        FieldPanel('name2'),
        StreamFieldPanel('body'),
        InlinePanel('test_related_model', label='Test Related Model', min_num=0, max_num=1),
        FieldPanel('content_release'),
    ]

    @property
    def site_code(self):
        """ site_code """
        return SiteSettings.objects.get(site=self.get_site()).slug

    def get_serializers(self):
        """ get_serializers """
        from .serializers import TestPageSerializer, TestPageCoverSerializer
        return {
            'default': {
                'key': self.get_key(),
                'type': self.get_name_slug(),
                'class': TestPageSerializer,
            },
            'cover': {
                'key': self.get_key(),
                'type': 'cover',
                'class': TestPageCoverSerializer,
            }
        }

    @property
    def preview_modes(self):
        """
        A list of (internal_name, display_name) tuples for the modes in which
        this page can be displayed for preview/moderation purposes. Ordinarily a page
        will only have one display mode, but subclasses of Page can override this -
        for example, a page containing a form might have a default view of the form,
        and a post-submission 'thankyou' page
        """
        return [
            ('default', 'Default'),
            ('cover', 'Cover'),
        ]

    @property
    def default_preview_mode(self):
        """ default_preview_mode """
        return self.preview_modes[0][0]


class TestModel(ModelWithRelease):
    """ TestModel """
    name1 = models.CharField(max_length=255)
    name2 = models.CharField(max_length=255)

    body = StreamField([
        ('simple_richtext', SimpleRichText(icon='title')),
        ('dynamictestpage_block', DynamicTestPageBlock('test_page.TestPage')),
    ], blank=True, null=True)

    release_config = {
        'can_publish_to_release': True,
        'can_publish_to_live_release': True,
    }

    panels = ModelWithRelease.panels + [
        FieldPanel('name1'),
        FieldPanel('name2'),
        StreamFieldPanel('body'),
    ]

    def get_serializers(self):
        """ get_serializers """
        from .serializers import TestModelSerializer, TestModelCoverSerializer
        return {
            'default': {
                'key': self.get_key(),
                'type': self.get_name_slug(),
                'class': TestModelSerializer,
            },
            'cover': {
                'key': self.get_key(),
                'type': 'cover',
                'class': TestModelCoverSerializer,
            }
        }

    def get_key(self):
        """ get_key """
        return 'test_model'

    def __str__(self):
        """ __str__ """
        return '{} - {}'.format(self.name1, self.name2)

    def get_redirections(self):
        """ get_redirections """
        redirects = Redirect.objects.all()

        redirect_objects = []

        for redirect in redirects:
            redirect_object = model_to_dict(redirect)
            del redirect_object['id']
            del redirect_object['site']
            if redirect_object['redirect_page']:
                redirect_object['redirect_link'] = Page.objects.get(id=4).url
                del redirect_object['redirect_page']
            else:
                del redirect_object['redirect_page']
            redirect_objects.append(redirect_object)

        return redirect_objects

    @property
    def preview_modes(self):
        """
        A list of (internal_name, display_name) tuples for the modes in which
        this page can be displayed for preview/moderation purposes. Ordinarily a page
        will only have one display mode, but subclasses of Page can override this -
        for example, a page containing a form might have a default view of the form,
        and a post-submission 'thankyou' page
        """
        return [
            ('default', 'Default'),
            ('cover', 'Cover'),
        ]


@receiver(post_save, sender=SiteSettings)
@receiver(post_delete, sender=SiteSettings)
def update_site_code_widget_for_content_release(sender, instance, **kwargs):
    """ update_site_code_widget_for_content_release """
    from django import forms
    from wagtail.admin.edit_handlers import FieldPanel
    from wagtailsnapshotpublisher.models import WSSPContentRelease, ModelWithRelease

    site_settings = SiteSettings.objects.exclude(title='').values_list('slug', 'slug')

    site_code_widget = forms.Select(
        choices=tuple([('', '---------')] + list(site_settings)),
    )

    WSSPContentRelease.get_panel_field('site_code').widget = site_code_widget
    ModelWithRelease.get_panel_field('site_code').widget = site_code_widget


try:
    update_site_code_widget_for_content_release(SiteSettings, None)
except ProgrammingError:
    pass


@receiver(pre_save, sender=SiteSettings)
def update_site_code_for_content_release(sender, instance, **kwargs):
    from wagtailsnapshotpublisher.models import WSSPContentRelease
    try:
        old_instance = SiteSettings.objects.get(id=instance.id)
        if old_instance.slug != instance.slug:
            WSSPContentRelease.objects.filter(
                site_code=old_instance.slug,
            ).update(site_code=instance.slug)
    except SiteSettings.DoesNotExist:
        pass
