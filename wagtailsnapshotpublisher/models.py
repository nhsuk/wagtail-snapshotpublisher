"""
.. module:: wagtailsnapshotpublisher.models
"""

import json
import re

from django import forms, dispatch

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count, Min
from django.db.models.query import QuerySet
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, HelpPanel
from wagtail.core.models import Page, PageRevision

from djangosnapshotpublisher.models import ContentRelease
from djangosnapshotpublisher.publisher_api import PublisherAPI

from .panels import ReadOnlyPanel
from .utils import get_from_dict, set_in_dict, del_in_dict, get_dynamic_element_keys
from .signals import content_was_published

site_code_widget = None

if settings.SITE_CODE_CHOICES:
    site_code_widget = forms.Select(
        choices=settings.SITE_CODE_CHOICES,
    )

VERSION_TYPES = (
    (0, 'MAJOR'),
    (1, 'MINOR'),
)


class WSSPContentRelease(ContentRelease):
    """ WSSPContentRelease """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='release_author',
    )
    publisher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='release_publisher',
    )
    version_type = models.IntegerField(choices=VERSION_TYPES, default=1)
    restored = models.BooleanField(default=False)

    structure_to_store = {
        'fields': ['id'],
    }

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('site_code', widget=site_code_widget),
                ReadOnlyPanel('uuid'),
                ReadOnlyPanel('get_status_display', heading='Status'),
                FieldPanel('title'),
                FieldPanel('version_type', widget=forms.RadioSelect),
                ReadOnlyPanel('version'),
            ],
            heading='General',
        ),
        MultiFieldPanel(
            [
                FieldPanel('use_current_live_as_base_release'),
                FieldPanel('base_release'),
                HelpPanel(_(
                    'If you active the current live release, the base release will be ignore')),
            ],
            heading='Publishing',
        )
    ]

    panels_live_release = [
        MultiFieldPanel(
            [
                ReadOnlyPanel('author'),
                ReadOnlyPanel('publisher'),
                ReadOnlyPanel('site_code'),
                ReadOnlyPanel('uuid'),
                ReadOnlyPanel('get_status_display', heading='Status'),
                ReadOnlyPanel('title'),
                ReadOnlyPanel('version'),
            ],
            heading='General',
        ),
        MultiFieldPanel(
            [
                ReadOnlyPanel('use_current_live_as_base_release'),
                ReadOnlyPanel('base_release'),
                ReadOnlyPanel('publish_datetime'),
            ],
            heading='Publishing',
        )
    ]


    def __str__(self):
        return '[[{0}]] {1} - {2}__{3}'.format(
            self.site_code, self.version, self.title, self.get_status_display())

    class Meta:
        """ Meta """
        verbose_name = 'Release'

    @classmethod
    def get_panel_field(cls, field_name):
        """ get_panel_field """
        panels = cls.panels
        return cls.get_panel_field_from_panels(panels, field_name)

    @classmethod
    def get_panel_field_from_panels(cls, panels, field_name):
        """ get_panel_field_from_panels """
        for i, item in enumerate(panels):
            if hasattr(item, 'field_name') and item.field_name == field_name:
                return item
            if hasattr(item, 'children'):
                return cls.get_panel_field_from_panels(item.children, field_name)
        return None


@receiver(pre_save, sender=WSSPContentRelease)
def define_version(sender, instance, *args, **kwargs):
    """ define_version """
    if not instance.version and instance.status != 0:
        previous_version = '0.0'

        # get previous release
        content_releases = WSSPContentRelease.objects.filter(
            site_code=instance.site_code,
        ).exclude(
            status=0,
        ).exclude(
            id=instance.id,
        )
        if instance.publish_datetime:
            content_releases = content_releases.exclude(
                publish_datetime=None,
            ).exclude(
                publish_datetime__gt=instance.publish_datetime,
            )

        content_releases = content_releases.order_by('-version')

        if content_releases.exists():
            previous_version = content_releases.first().version

        version_list = previous_version.split('.')
        # i=0
        for i, item in enumerate(version_list):
            if i == instance.version_type:
                version_list[i] = str(int(item) + 1)
            if i > instance.version_type:
                version_list[i] = '0'

        next_version = '.'.join(version_list)
        instance.version = next_version
        return instance


@receiver(post_save, sender=WSSPContentRelease)
def fix_versions_conflict(sender, instance, *args, **kwargs):
    """ fix_versions_conflict """
    duplicate_version = WSSPContentRelease.objects.filter(
                site_code=instance.site_code,
        ).values(
            'version'
        ).annotate(
            count_same_version=Count('version')
        ).exclude(count_same_version__lte=1)

    if duplicate_version:
        # get min version from duplicate_version
        min_version = duplicate_version.aggregate(Min('version'))['version__min']

        releases_to_update = WSSPContentRelease.objects.filter(
            site_code=instance.site_code,
            version__gte=min_version,
        ).order_by('publish_datetime')

        # reset version
        for release in releases_to_update:
            content_release = ContentRelease.objects.get(id=release.id)
            content_release.version = None
            content_release.save()

        # update version
        for release in releases_to_update:
            release.version = None
            release = define_version(WSSPContentRelease, release)
            release.save()


@receiver(post_save, sender=ContentRelease)
@receiver(post_save, sender=WSSPContentRelease)
def load_dynamic_element(sender, instance, *args, **kwargs):
    """ load_dynamic_element """
    if instance.is_live:
        # get all ReleaseContent with dynamic element
        release_documents = instance.release_documents.filter(
            parameters__key='have_dynamic_elements',
            parameters__content=True,
        )

        for release_document in release_documents:
            content, updated = document_load_dynamic_elements(
                instance,
                json.loads(release_document.document_json)
            )
            if updated:
                release_document.document_json = json.dumps(content)
                release_document.save()


def document_load_dynamic_elements(content_release, content):
    """ document_load_dynamic_elements """
    updated = False

    if 'dynamic_element_keys' in content:
        elements_to_remove = []

        for elt_list in content['dynamic_element_keys']:
            item = get_from_dict(content, elt_list)

            try:
                model = apps.get_model(item['app'], item['class'])
                loaded_instance = model.objects.get(id=item['id'])
                item_serializer = loaded_instance.get_serializers()[item['serializer']]

                publisher_api = PublisherAPI()
                response = publisher_api.get_document_from_content_release(
                    content_release.site_code,
                    content_release.uuid,
                    item_serializer['key'],
                    item_serializer['type'],
                )

                if response['status'] == 'success':
                    set_in_dict(content, elt_list, json.loads(response['content'].document_json))
                else:
                    raise Exception(response['error_msg'])
            except:
                elements_to_remove.append(elt_list[:-1])

        #save document with loaded dynamic content
        for element_to_remove in elements_to_remove[::-1]:
            del_in_dict(content, element_to_remove)
        del content['dynamic_element_keys']
        updated = True

    return content, updated


class WithRelease(models.Model):
    """ WithRelease """
    content_release = models.ForeignKey(
        WSSPContentRelease,
        related_name='%(class)s_content_release',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(status=0) | Q(status=1),
    )

    class Meta:
        """ Meta """
        abstract = True

    @property
    def live_release(self):
        """ live_release """
        if self.content_release:
            return WSSPContentRelease.objects.live(site_code=self.content_release.site_code)
        return None

    def get_key(self):
        """ get_key """
        return self.id

    def get_name_slug(self):
        """ get_name_slug from classname"""
        snake_case = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.__class__.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case).lower()

    def get_serializers(self):
        """ get_serializers """
        raise ValueError(_('get_serializers is not define'))

    def publish_to_release(self, instance=None, content_release=None, extra_parameters={}):
        """ publish_to_release """
        if not instance:
            instance = self

        if not content_release:
            content_release = self.content_release

        serializers = self.get_serializers()

        for key, serializer_item in serializers.items():
            have_dynamic_elements = False
            serialized_page = serializer_item['class'](instance=self)
            data = serialized_page.data

            dynamic_element_keys = get_dynamic_element_keys(data)
            if dynamic_element_keys:
                data.update({
                    'dynamic_element_keys': dynamic_element_keys,
                })
                have_dynamic_elements = True

            extra_parameters.update({
                'have_dynamic_elements': have_dynamic_elements,
            })

            publisher_api = PublisherAPI()
            json_data = json.dumps(data)
            response = publisher_api.publish_document_to_content_release(
                content_release.site_code,
                content_release.uuid,
                json_data,
                serializer_item['key'],
                serializer_item['type'],
                extra_parameters,
            )

            if response['status'] == 'success':
                content_was_published.send(sender=self.__class__, site_id=content_release.site_code, release_id=content_release.uuid, title=data.get("title"), content=json_data)
            else:
                raise Exception(response['error_msg'])


    def unpublish_or_delete_from_release(self, release_id, recursively=False, delete=False):
        """ unpublish_or_delete_from_release """
        if recursively:
            for child_page in self.get_children():
                try:
                    child_page.specific.unpublish_or_delete_from_release(
                        release_id, recursively, delete)
                except AttributeError:
                    pass
        content_release = WSSPContentRelease.objects.get(id=release_id)
        publisher_api = PublisherAPI()

        serializers = self.get_serializers()
        for key, serializer_item in serializers.items():
            paramaters = {
                'site_code': content_release.site_code,
                'release_uuid': content_release.uuid,
                'document_key': serializer_item['key'],
                'content_type': serializer_item['type'],
            }

            response = None
            if delete:
                response = publisher_api.delete_document_from_content_release(**paramaters)
            else:
                response = publisher_api.unpublish_document_from_content_release(**paramaters)

            if response['status'] != 'success':
                raise Exception(response['error_msg'])


class ModelWithRelease(WithRelease):
    """ ModelWithRelease """
    site_code = models.SlugField(max_length=100, blank=True, null=True)
    publish_to_live_release = models.BooleanField(default=False)

    panels = [
        FieldPanel('site_code', widget=site_code_widget),
        FieldPanel('publish_to_live_release'),
        FieldPanel('content_release'),
    ]

    class Meta:
        """ Meta """
        abstract = True

    def get_app(self):
        """ get_app """
        return self.__class__._meta.app_label

    def get_class(self):
        """ get_class """
        return self.__class__.__name__.lower()

    def clean(self):
        """ clean """
        super().clean()

        # get live release
        if self.publish_to_live_release:
            self.publish_to_live_release = False
            publisher_api = PublisherAPI()
            response = publisher_api.get_live_content_release(self.site_code)
            if response['status'] == 'error':
                raise ValidationError({'site_code': response['error_msg']})

            self.content_release = WSSPContentRelease.objects.get(id=response['content'].id)


    def save(self, *args, **kwargs):
        """ save """
        if self.content_release:
            self.publish_to_release()
        super().save(*args, **kwargs)

    @classmethod
    def get_panel_field(cls, field_name):
        """ get_panel_field """
        panels = cls.panels
        return cls.get_panel_field_from_panels(panels, field_name)

    @classmethod
    def get_panel_field_from_panels(cls, panels, field_name):
        """ get_panel_field_from_panels """
        for i, item in enumerate(panels):
            if hasattr(item, 'field_name') and item.field_name == field_name:
                return item
            if hasattr(item, 'children'):
                return cls.get_panel_field_from_panels(item.children, field_name)
        return None


class PageWithRelease(Page, WithRelease):
    """ PageWithRelease """
    class Meta:
        """ Meta """
        abstract = True

    def get_name_slug(self):
        """ get_name_slug """
        return 'page'

    def serve_preview(self, request, mode_name='default', load_dynamic_element=False):
        """ serve_preview """
        request.is_preview = True
        serializers = self.get_serializers()
        mode_name = mode_name if mode_name else 'default'
        serialized_page = serializers[mode_name]['class'](instance=self)
        data = serialized_page.data

        if load_dynamic_element:
            dynamic_element_keys = get_dynamic_element_keys(data)
            if dynamic_element_keys and len(dynamic_element_keys) > 0:
                data.update({
                    'dynamic_element_keys': dynamic_element_keys,
                })
                data, updated = document_load_dynamic_elements(self.live_release, data)
        return JsonResponse(data)

    def save_revision(self, user=None, submitted_for_moderation=False, approved_go_live_at=None,
                      changed=True):
        """ save_revision """
        assigned_release = self.content_release
        self.content_release = None

        revision = super(PageWithRelease, self).save_revision(
            user, submitted_for_moderation, approved_go_live_at, changed)
        revision.publish()

        if assigned_release:
            # if submitted_for_moderation:
            #     pass
            # else:
            page = revision.as_page_object()
            self.publish_to_release(page, assigned_release, {'revision_id': revision.id})

        return revision
