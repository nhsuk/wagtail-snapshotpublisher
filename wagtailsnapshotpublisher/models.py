import json
import re

from django import forms
from django.db import models
from django.conf import settings
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, HelpPanel
from wagtail.core.models import Page, PageRevision

from djangosnapshotpublisher.models import ContentRelease
from djangosnapshotpublisher.publisher_api import PublisherAPI

from .json_encoder import StreamFieldEncoder
from .panels import ReadOnlyPanel


site_code_widget = None

if settings.SITE_CODE_CHOICES:
    site_code_widget = forms.Select(
        choices=settings.SITE_CODE_CHOICES,
    )


class WSSPContentRelease(ContentRelease):

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('site_code', widget=site_code_widget),
                ReadOnlyPanel('uuid'),
                FieldPanel('status'),
                FieldPanel('title'),
                FieldPanel('version'),
            ],
            heading='General',
        ),
        MultiFieldPanel(
            [
                FieldPanel('use_current_live_as_base_release'),
                FieldPanel('base_release'),
                FieldPanel('publish_datetime'),
                HelpPanel(_('If you active the current live release, the base release will be ignore')),
            ],
            heading='Publishing',
        )
    ]

    def __str__(self):
        return '{0} - {1}'.format(self.version, self.title)

    class Meta:
        verbose_name = 'Releases'

    @classmethod
    def get_panel_field(cls, field_name):
        panels = cls.panels
        return cls.get_panel_field_from_panels(panels, field_name)

    @classmethod
    def get_panel_field_from_panels(cls, panels, field_name):
        for i in range(len(panels)):
            if hasattr(panels[i], 'field_name') and panels[i].field_name == field_name:
                return(panels[i])
            if hasattr(panels[i], 'children'):
                return cls.get_panel_field_from_panels(panels[i].children, field_name)
        return None


class WithRelease(models.Model):
    content_release = models.ForeignKey(
        WSSPContentRelease,
        related_name='%(class)s_content_release',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        limit_choices_to={'status': 0})

    class Meta:
        abstract = True

    def get_key(self):
        return self.id

    def get_name_slug(self):
        if hasattr(self.__class__, 'slug_name') and self.__class__.slug_name:
            return self.slug_name
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.__class__.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


    @classmethod
    def document_parser(cls, item, schema, model_as_dict):
        # get fields and data
        object_dict = {key: value  for key, value in model_as_dict.items() if key in schema['fields']}

        if 'extra' in schema:
            for extra in schema['extra']:
                object_dict.update({
                    extra['name']: getattr(item, extra['function'])(),
                })

        # get related fields and data
        if 'related_fields' in schema:
            for related_field in schema['related_fields']:
                related_field_data = getattr(item, 'test_related_model').all()
                if related_field_data.exists():
                    if related_field_data.count() > 1:
                        object_dict.update(
                            {
                                related_field: [cls.document_parser(related_item, related_item.__class__.structure_to_store, model_to_dict(related_item)) for related_item in related_field_data.all()]
                            }
                        )
                    else:
                        related_item = related_field_data.first()
                        object_dict.update(
                            {
                                related_field: cls.document_parser(related_item, related_item.__class__.structure_to_store, model_to_dict(related_item))
                            }
                        )

        # get children
        if 'children' in schema:
            for schema_child in schema['children']:
                object_dict.update(
                    {schema_child['name']: cls.document_parser(item, schema_child, model_as_dict)}
                )

        return object_dict


    def publish_to_release(self, instance=None, content_release=None):
        if not instance:
            instance = self

        if not content_release:
            content_release = self.content_release
        
        object_dict = self.__class__.document_parser(self, self.__class__.structure_to_store, model_to_dict(self))

        publisher_api = PublisherAPI()
        response = publisher_api.publish_document_to_content_release(
            content_release.site_code,
            content_release.uuid,
            json.dumps(object_dict, cls=StreamFieldEncoder),
            self.get_key(),
            self.get_name_slug(),
        )

    def unpublish_from_release(self, release_id=None, recursively=False):
        if not release_id:
            pass
        else:
            if recursively:
                for child_page in self.get_children():
                    try:
                        child_page.specific.unpublish_from_release(release_id, recursively)
                    except AttributeError:
                        pass
            content_release = WSSPContentRelease.objects.get(id=release_id)
            publisher_api = PublisherAPI()
            reponse = publisher_api.unpublish_document_from_content_release(
                content_release.site_code,
                content_release.uuid,
                self.get_key(),
                self.get_name_slug(),
            )


class ModelWithRelease(WithRelease):

    class Meta:
        abstract = True

    def get_app(self):
        return self.__class__._meta.app_label

    def get_class(self):
        return self.__class__.__name__.lower()

    def save(self, *args, **kwargs):
        if self.content_release:
            self.publish_to_release()
        super().save(*args, **kwargs)


class PageWithRelease(Page, WithRelease):

    class Meta:
        abstract = True
    
    def get_name_slug(self):
        return 'page'

    def save_revision(self, user=None, submitted_for_moderation=False, approved_go_live_at=None, changed=True):
        assigned_release = self.content_release
        self.content_release = None

        revision = super(PageWithRelease, self).save_revision(user, submitted_for_moderation, approved_go_live_at, changed)

        if assigned_release:
            if submitted_for_moderation:
                pass
            else:
                page = revision.as_page_object()
                self.publish_to_release(page, assigned_release)

        return revision


    def serve_preview(self, request, mode_name):
        object_dict = self.__class__.document_parser(self.specific, self.specific.__class__.structure_to_store, model_to_dict(self.specific))
        return JsonResponse(object_dict, encoder=StreamFieldEncoder)
