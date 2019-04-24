import json
import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count, Min
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
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

VERSION_TYPES = (
    (0, 'MAJOR'),
    (1, 'MINOR'),
    # (2, 'PATCH'),
)


class WSSPContentRelease(ContentRelease):

    version_type = models.IntegerField(choices=VERSION_TYPES, default=1)
    restored = models.BooleanField(default=False)

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
                FieldPanel('publish_datetime'),
                HelpPanel(_('If you active the current live release, the base release will be ignore')),
            ],
            heading='Publishing',
        )
    ]

    def __str__(self):
        return '[[{0}]] {1} - {2}__{3}'.format(
            self.site_code, self.version, self.title, self.get_status_display())

    class Meta:
        verbose_name = 'Release'

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


@receiver(pre_save, sender=WSSPContentRelease)
def define_version(sender, instance, *args, **kwargs):
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
        i=0
        for i in range(len(version_list)):
            if i == instance.version_type:
                version_list[i] = str(int(version_list[i]) + 1)
            if i > instance.version_type:
                version_list[i] = '0'
            i += 1

        next_version = '.'.join(version_list)
        instance.version = next_version
        return instance

@receiver(post_save, sender=WSSPContentRelease)
def fix_versions_conflict(sender, instance, *args, **kwargs):
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


class WithRelease(models.Model):
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
        abstract = True

    @property
    def live_releave(self):
        return WSSPContentRelease.objects.live(site_code=self.site_code)

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


    def publish_to_release(self, instance=None, content_release=None, extra_parameters=None):
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
            extra_parameters,
        )

    def unpublish_or_delete_from_release(self, release_id=None, recursively=False, delete=False):
        if not release_id:
            pass
        else:
            if recursively:
                for child_page in self.get_children():
                    try:
                        child_page.specific.unpublish_or_delete_from_release(
                            release_id, recursively, delete)
                    except AttributeError:
                        pass
            content_release = WSSPContentRelease.objects.get(id=release_id)
            publisher_api = PublisherAPI()

            paramaters = {
                'site_code': content_release.site_code,
                'release_uuid': content_release.uuid,
                'document_key': self.get_key(),
                'content_type': self.get_name_slug(),
            }

            if delete:
                reponse = publisher_api.delete_document_from_content_release(**paramaters)
            else:
                reponse = publisher_api.unpublish_document_from_content_release(**paramaters)


class ModelWithRelease(WithRelease):

    site_code = models.SlugField(max_length=100)
    publish_to_live_release = models.BooleanField(default=False)

    panels = [
        FieldPanel('site_code', widget=site_code_widget),
        FieldPanel('publish_to_live_release'),
    ]

    class Meta:
        abstract = True

    def get_app(self):
        return self.__class__._meta.app_label

    def get_class(self):
        return self.__class__.__name__.lower()
    
    def clean(self):
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
                self.publish_to_release(page, assigned_release, {'revision_id': revision.id})

        return revision


    def serve_preview(self, request, mode_name):
        object_dict = self.__class__.document_parser(self.specific, self.specific.__class__.structure_to_store, model_to_dict(self.specific))
        return JsonResponse(object_dict, encoder=StreamFieldEncoder)
