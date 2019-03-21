import json
import re

from django import forms
from django.db import models
from django.conf import settings
from django.forms.models import model_to_dict

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page

from djangosnapshotpublisher.models import ContentRelease
from djangosnapshotpublisher.publisher_api import PublisherAPI

from .panels import ReadOnlyPanel


site_code_widget = None

if settings.SITE_CODE_CHOICES:
    site_code_widget = forms.Select(
        choices=settings.SITE_CODE_CHOICES,
    )

class WSSPContentRelease(ContentRelease):

    panels = [
        ReadOnlyPanel('uuid'),
        FieldPanel('title'),
        FieldPanel('site_code', widget=site_code_widget),
        FieldPanel('version'),
        FieldPanel('status'),
        FieldPanel('base_release'),
        FieldPanel('publish_datetime'),
    ]

    def __str__(self):
        return '{0} - {1}'.format(self.version, self.title)

    class Meta:
        verbose_name = 'Releases'


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

    def publish_to_release(self, instance=None, content_release=None):
        if not instance:
            instance = self

        if not content_release:
            content_release = self.content_release
        
        object_dict = {key: value  for key, value in model_to_dict(self).items() if key in self.__class__.fields_to_store}

        publisher_api = PublisherAPI()
        response = publisher_api.publish_document_to_content_release(
            content_release.site_code,
            content_release.uuid,
            json.dumps(object_dict),
            self.get_key(),
            self.get_name_slug(),
        )

    def unpublish_from_release(self, release_id=None):
        if not release_id:
            pass
        else:
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

    def save(self, *args, **kwargs):
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
