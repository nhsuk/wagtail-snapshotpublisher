"""
.. module:: tests.tests_forms
"""

import json

from django.db.models import Q
from django.utils import timezone

from wagtail.tests.utils import WagtailPageTests

from wagtailsnapshotpublisher.models import WSSPContentRelease
from wagtailsnapshotpublisher.forms import PublishReleaseForm, FrozenReleasesForm


class PublishReleaseFormTests(WagtailPageTests):
    """ FormTests """

    def setUp(self):
        """ setUp """

    def test_form_clean(self):
        """ test_form_clean """

        # publish_datetime in the future
        data = {
            'publish_type': 'schedule_date',
            'publish_datetime': timezone.now() + timezone.timedelta(hours=1),
        }
        form = PublishReleaseForm(data)
        self.assertTrue(form.is_valid())

        # publish_datetime in the past
        data = {
            'publish_type': 'schedule_date',
            'publish_datetime': timezone.now() - timezone.timedelta(hours=1),
        }
        form = PublishReleaseForm(data)
        self.assertFalse(form.is_valid())
        publish_datetime_errors = json.loads(form['publish_datetime'].errors.as_json())
        publish_datetime_error_codes = [publish_datetime_error['code'] \
            for publish_datetime_error in publish_datetime_errors]
        self.assertTrue('publish_datetime_in_future' in publish_datetime_error_codes)


class FrozenReleasesFormTests(WagtailPageTests):
    """ FrozenReleasesFormTests """

    def setUp(self):
        """ setUp """

    def test_form_init(self):
        """ test_form_init """

        # Create ContentRelease1
        content_release1 = WSSPContentRelease(
            title='release1',
            site_code='site1',
            version='0.1',
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(hours=1),
        )
        content_release1.save()

        # one live release
        data = {}
        form = FrozenReleasesForm('site1', data)
        self.assertTrue(form.fields['releases'].queryset is None)

        # Create ContentRelease
        content_release2 = WSSPContentRelease(
            title='release2',
            site_code='site1',
            version='0.2',
            status=1,
            publish_datetime=timezone.now() + timezone.timedelta(hours=1),
        )
        content_release2.save()

        content_release3 = WSSPContentRelease(
            title='release3',
            site_code='site1',
            version='0.3',
            status=0,
            publish_datetime=timezone.now() + timezone.timedelta(hours=2),
        )
        content_release3.save()

        content_release4 = WSSPContentRelease(
            title='release4',
            site_code='site2',
            version='0.4',
            status=1,
            publish_datetime=timezone.now() + timezone.timedelta(hours=2),
        )
        content_release4.save()

        content_release5 = WSSPContentRelease(
            title='release5',
            site_code='site1',
            version='0.5',
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(hours=2),
        )
        content_release5.save()

        content_release6 = WSSPContentRelease(
            title='release6',
            site_code='site1',
            version='0.6',
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(hours=2),
        )
        content_release6.save()

        data = {}
        form = FrozenReleasesForm('site1', data)
        self.assertEqual(form.fields['releases'].queryset.count(), 2)
        self.assertQuerysetEqual(form.fields['releases'].queryset,
                                 WSSPContentRelease.objects.filter(
                                     Q(title='release1') | Q(title='release2')
                                 ).order_by('publish_datetime', 'title'), transform=lambda x: x)
