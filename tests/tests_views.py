"""
.. module:: tests.tests_views
"""

import os
import uuid

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import Http404
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from djangosnapshotpublisher.models import ReleaseDocument
from djangosnapshotpublisher.publisher_api import PublisherAPI, DATETIME_FORMAT

from wagtailsnapshotpublisher.models import WSSPContentRelease
from wagtailsnapshotpublisher.views import *
from wagtailsnapshotpublisher.wagtail_hooks import ReleaseAdmin

from test_page.models import TestModel, TestPage, TestRelatedModel


class WagtailSnapshotPublisherViewTests(TestCase):
    """ WagtailSnapshotPublisherViewTests """

    @classmethod
    def setUpTestData(cls):
        """ setUpTestData """
        call_command('load_test_data_fixtures', '--no-output')

    def setUp(self):
        """ setUp """
        User = get_user_model()
        username = os.environ.get('CMS_SUPERUSER_USERNAME', 'superadmin')
        self.user = User.objects.get(username=username)
        self.page1 = TestPage.objects.get(id=3)
        self.page2 = TestPage.objects.get(id=4)
        self.test_model = TestModel.objects.get(id=1)
        self.content_release = WSSPContentRelease.objects.get(id=1)
        self.publisher_api = PublisherAPI(api_type='django')
        self.factory = RequestFactory()
        self.client =  Client()
        self.client.force_login(self.user)
        self.url_release_admin_index = ReleaseAdmin().url_helper.index_url

    def test_unpublish_page(self):
        """ test_unpublish_page """
        self.assertEqual(ReleaseDocument.objects.all().count(), 0)
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)
        self.assertEqual(ReleaseDocument.objects.all().count(), 2)

        url = reverse('wagtailsnapshotpublisher_admin:unpublish_page_from_release', kwargs={
            'page_id': self.page1.id,
            'release_id': self.content_release.id,
        })
        request = self.factory.post(url)
        request.user = self.user
        
        view_response = unpublish_page(request, self.page1.id, self.content_release.id)

        self.assertEqual(view_response.status_code, 302)
        self.assertEqual(ReleaseDocument.objects.all().count(), 0)

    def test_get_document_release(self):
        """ test_get_document_release """
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)

        url = reverse('wagtailsnapshotpublisher_api:live_document_release_page', kwargs={
            'site_code': self.content_release.site_code,
            'content_type': self.content_release.uuid,
            'content_key': self.page1.id,
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = get_document_release(
            request,
            self.content_release.site_code,
            self.content_release.uuid,
            'page',
            self.page1.id,
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'title': 'Test1',
            'name1': 'Name1',
            'test_related_model': [1],
            'body': [
                {
                    'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86',
                    'type': 'simple_richtext',
                    'value': {
                        'title': 'Title1',
                        'body': '<p>Body1</p>'
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8',
                    'value': {
                        'title': 'Test1',
                        'name1': 'Name1',
                    },
                }
            ],
        })

    def test_get_document_release_wrong_uuid(self):
        """ test_get_document_release_wrong_uuid """
        url = reverse('wagtailsnapshotpublisher_api:document_release_page', kwargs={
            'site_code': self.content_release.site_code,
            'content_release_uuid': uuid.uuid4(),
            'content_type': 'page',
            'content_key': self.page1.id,
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = get_document_release(
            request,
            self.content_release.site_code,
            uuid.uuid4(),
            'page',
            self.page1.id,
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content)['status'], 'error')
        self.assertEqual(json.loads(view_response.content)['error_code'],
                         'content_release_does_not_exist')

    def test_get_document_release_wrong_site_code(self):
        """ test_get_document_release_wrong_site_code """
        url = reverse('wagtailsnapshotpublisher_api:live_document_release_page', kwargs={
            'site_code': 'wrong_site_code',
            'content_type': 'page',
            'content_key': self.page1.id,
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = get_document_release(
            None,
            'wrong_site_code',
            None,
            'page',
            self.page1.id,
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content)['status'], 'error')
        self.assertEqual(json.loads(view_response.content)['error_code'],
                         'no_content_release_live')

    def test_get_document_release_with_live_release(self):
        """ test_get_document_release_with_live_release """
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)
        response = self.publisher_api.set_live_content_release(self.content_release.site_code,
                                                               self.content_release.uuid)

        url = reverse('wagtailsnapshotpublisher_api:live_document_release_page', kwargs={
            'site_code': self.content_release.site_code,
            'content_type': 'page',
            'content_key': self.page1.id,
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = get_document_release(
            request,
            self.content_release.site_code,
            None,
            'page',
            self.page1.id,
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'title': 'Test1',
            'name1': 'Name1',
            'test_related_model': [1],
            'body': [
                {
                    'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86',
                    'type': 'simple_richtext',
                    'value': {
                        'title': 'Title1',
                        'body': '<p>Body1</p>'
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8',
                    'value': {'title': 'Test1', 'name1': 'Name1'}
                }
            ],
        })

    def test_remove(self):
        """ test_remove """
        self.assertEqual(ReleaseDocument.objects.all().count(), 0)
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)
        self.assertEqual(ReleaseDocument.objects.all().count(), 2)

        remove(None, 'test_page', 'TestPage', self.page1.id, self.content_release.id)

        self.assertEqual(ReleaseDocument.objects.all().count(), 2)
        self.assertEqual(ReleaseDocument.objects.filter(deleted=True).count(), 2)

    def test_preview_instance_default(self):
        """ test_preview_instance """
        self.page1.title = 'Test Preview'
        self.page1.name1 = 'Name1 Preview'
        self.page1.save()

        url = reverse('wagtailsnapshotpublisher_admin:preview_instance_admin', kwargs={
            'content_app': 'test_page',
            'content_class': 'TestPage',
            'content_id': self.page1.id,
            'preview_mode': 'default',
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = preview_instance(
            request,
            'test_page',
            'TestPage',
            self.page1.id,
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'title': 'Test Preview',
            'name1': 'Name1 Preview',
            'test_related_model': [1],
            'body': [
                {
                    'type': 'simple_richtext',
                    'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86',
                    'value': {
                        'title': 'Title1',
                        'body': '<p>Body1</p>',
                    },
                },
            ],
        })

    def test_preview_instance_default_with_dynamic_elements(self):
        """ test_preview_instance """
        self.page1.title = 'Test Preview'
        self.page1.name1 = 'Name1 Preview'
        self.page1.save()
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)
        self.page2.content_release = self.content_release
        self.page2.save_revision(self.user)
        self.publisher_api.set_live_content_release(self.content_release.site_code,
                                                    self.content_release.uuid)

        self.page1.content_release = self.content_release
        self.page1.save()
        self.page2.content_release = self.content_release
        self.page2.save()

        url = reverse('wagtailsnapshotpublisher_admin:preview_instance_admin', kwargs={
            'content_app': 'test_page',
            'content_class': 'TestPage',
            'content_id': self.page1.id,
            'preview_mode': 'default',
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = preview_instance(
            request,
            'test_page',
            'TestPage',
            self.page1.id,
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'title': 'Test Preview',
            'name1': 'Name1 Preview',
            'test_related_model': [1],
            'body': [
                {
                    'type': 'simple_richtext',
                    'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86',
                    'value': {
                        'title': 'Title1',
                        'body': '<p>Body1</p>',
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8',
                    'value': {
                        'title': 'Test Preview',
                        'name1': 'Name1 Preview'
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '26ab3837-c224-4b28-bd29-24e0b38c0981',
                    'value': {
                        'title': 'Test2',
                        'name1': 'Test2 name1'
                    },
                }
            ],
        })

        url = reverse('wagtailadmin_pages:preview_on_edit', args=[self.page1.id])
        request = self.factory.post(url)
        request.user = self.user

        preview_response = self.page1.serve_preview(request)
        self.assertEqual(preview_response.status_code, 200)
        self.assertEqual(json.loads(preview_response.content), {
            'title': 'Test Preview',
            'name1': 'Name1 Preview',
            'test_related_model': [1],
            'body': [
                {
                    'type': 'simple_richtext',
                    'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86',
                    'value': {
                        'title': 'Title1',
                        'body': '<p>Body1</p>',
                    },
                },{
                    'type': 'dynamictestpage_block',
                    'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8',
                    'value': {
                        'id': 3,
                        'serializer': 'cover',
                        'dynamic': True,
                        'app': 'test_page',
                        'class': 'TestPage'
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '26ab3837-c224-4b28-bd29-24e0b38c0981',
                    'value': {
                        'id': 4,
                        'serializer': 'cover',
                        'dynamic': True,
                        'app': 'test_page',
                        'class': 'TestPage'
                    },
                }
            ],
        })

        preview_with_dynamic_elements_view = self.page1.serve_preview(request, 'default', True)
        self.assertEqual(preview_with_dynamic_elements_view.status_code, 200)
        self.assertEqual(json.loads(preview_with_dynamic_elements_view.content), {
            'title': 'Test Preview',
            'name1': 'Name1 Preview',
            'test_related_model': [1],
            'body': [
                {
                    'type': 'simple_richtext',
                    'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86',
                    'value': {
                        'title': 'Title1',
                        'body': '<p>Body1</p>',
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8',
                    'value': {
                        'title': 'Test Preview',
                        'name1': 'Name1 Preview'
                    },
                }, {
                    'type': 'dynamictestpage_block',
                    'id': '26ab3837-c224-4b28-bd29-24e0b38c0981',
                    'value': {
                        'title': 'Test2',
                        'name1': 'Test2 name1'
                    },
                }
            ],
        })

    def test_preview_instance_cover(self):
        """ test_preview_instance """
        self.page1.title = 'Test Preview'
        self.page1.name1 = 'Name1 Preview'
        self.page1.save()

        url = reverse('wagtailsnapshotpublisher_admin:preview_instance_admin', kwargs={
            'content_app': 'test_page',
            'content_class': 'TestPage',
            'content_id': self.page1.id,
            'preview_mode': 'cover',
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = preview_instance(
            request,
            'test_page',
            'TestPage',
            self.page1.id,
            'cover',
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'name1': 'Name1 Preview',
            'title': 'Test Preview',
        })

    def test_release_detail(self):
        """ test_release_detail """
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)
        self.publisher_api.set_live_content_release(self.content_release.site_code,
                                                    self.content_release.uuid)

        content_release2 = WSSPContentRelease.objects.get(id=2)
        self.page2.content_release = content_release2
        self.page2.save_revision(self.user)

        url = reverse('wagtailsnapshotpublisher_admin:release_detail', kwargs={
            'release_id': content_release2.id,
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = compare_release(
            request,
            content_release2.id,
        )
        
        self.assertEqual(view_response['release'], content_release2)
        self.assertEqual(view_response['release_to_compare_to'], self.content_release)
        self.assertEqual(view_response['compare_with_live'], True)

        url = reverse('wagtailsnapshotpublisher_admin:preview_instance_admin', kwargs={
            'content_app': 'test_page',
            'content_class': 'TestPage',
            'content_id': self.page1.id,
            'preview_mode': 'cover',
        })
        request = self.factory.post(url)
        request.user = self.user

        view_response = release_detail(
            request,
            content_release2.id,
        )

        self.assertEqual(view_response.status_code, 200)

    def test_release_set_live_then_unfreeze(self):
        """ test_release_set_live_then_unfreeze """

        # release_set_live
        self.assertEqual(self.content_release.status, 0)
        self.assertEqual(self.content_release.publish_datetime, None)
        url = reverse('wagtailsnapshotpublisher_admin:release_set_live', kwargs={
            'release_id': self.content_release.id,
        })
        client_response = self.client.get(url, follow=True)
        self.assertRedirects(
            client_response,
            self.url_release_admin_index,
            status_code=302,
            target_status_code=200,
        )
        self.content_release = WSSPContentRelease.objects.get(id=1)
        self.assertEqual(self.content_release.status, 1)
        self.assertTrue(self.content_release.publish_datetime < timezone.now())
        self.assertTrue(self.content_release.publish_datetime > timezone.now() - timezone.timedelta(minutes=3))

        # unfreeze
        url = reverse('wagtailsnapshotpublisher_admin:release_unfreeze', kwargs={
            'release_id': self.content_release.id,
        })
        client_response = self.client.get(url, follow=True)
        self.assertRedirects(
            client_response,
            self.url_release_admin_index,
            status_code=302,
            target_status_code=200,
        )
        self.content_release = WSSPContentRelease.objects.get(id=1)
        self.assertEqual(self.content_release.status, 0)
        self.assertEqual(self.content_release.publish_datetime, None)

    def test_release_unfreeze_wrong_id(self):
        """ test_release_unfreeze """
        url = reverse('wagtailsnapshotpublisher_admin:release_unfreeze', kwargs={
            'release_id': 999,
        })
        request = self.factory.post(url)
        request.user = self.user
        try:
            release_unfreeze(request, 999)
            self.assertFail('''A Http404 exception haven't been raise''')
        except Http404:
            pass

    def test_release_set_live_with_publish_date(self):
        """ test_release_set_live_with_publish_date """

        # publish_date in the past
        publish_datetime = timezone.now() - timezone.timedelta(minutes=5)

        try:
            release_set_live(
                None,
                self.content_release.id,
                publish_datetime.strftime(DATETIME_FORMAT),
            )
            self.assertFail('''A Http404 exception haven't been raise''')
        except Http404:
            pass

        # publish_date in the future
        publish_datetime = timezone.now() + timezone.timedelta(minutes=5)

        self.assertEqual(self.content_release.status, 0)
        self.assertEqual(self.content_release.publish_datetime, None)

        release_set_live(
            None,
            self.content_release.id,
            publish_datetime.strftime(DATETIME_FORMAT),
        )

        self.content_release = WSSPContentRelease.objects.get(id=1)
        self.assertEqual(self.content_release.status, 1)
        self.assertEqual(
            self.content_release.publish_datetime,
            publish_datetime.replace(microsecond=0),
        )

    def test_release_archive(self):
        """ test_release_archive """

        # archive content release not live content release
        try:
            release_archive(
                None,
                self.content_release.id,
            )
            self.assertFail('''A Http404 exception haven't been raise''')
        except Http404:
            pass

        # set live content release
        publish_datetime = timezone.now() - timezone.timedelta(minutes=5)
        self.content_release.status = 1
        self.content_release.publish_datetime = publish_datetime
        self.content_release.save()

        # archive content release
        url = reverse('wagtailsnapshotpublisher_admin:release_archive', kwargs={
            'release_id': self.content_release.id,
        })
        client_response = self.client.get(url, follow=True)
        self.assertRedirects(
            client_response,
            self.url_release_admin_index,
            status_code=302,
            target_status_code=200,
        )
        self.content_release = WSSPContentRelease.objects.get(id=1)
        self.assertEqual(self.content_release.status, 2)
        self.assertEqual(
            self.content_release.publish_datetime,
            publish_datetime,
        )

    def test_preview_model(self):
        """ test_preview_model """

        url = reverse('wagtailsnapshotpublisher_admin:preview_model_admin', kwargs={
            'content_app': 'test_page',
            'content_class': 'testmodel',
            'content_id': self.test_model.id,
            'preview_mode': 'default',
        })

        # wrong form for preview
        request = self.factory.post(url, {
            'wrongfield': 'Preview Test model2 name1',
            'body-count': ['0'],
        })
        view_response = preview_model(request, 'test_page', 'testmodel', self.test_model.id, 'default')
        self.assertEqual(view_response.status_code, 500)
        self.assertEqual(view_response.content, b'Form is not valid')

        # preview ok
        request = self.factory.post(url, {
            'name1': ['Preview Test model2 name1'],
            'name2': ['Preview Test model2 name2'],
            'body-count': ['0'],
        })
        view_response = preview_model(
            request, 'test_page', 'testmodel', self.test_model.id, 'default', True)

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'name1': 'Preview Test model2 name1',
            'name2': 'Preview Test model2 name2',
            'body': [],
            'redirects': []
        })

        # preview with dynamic content
        self.page1.content_release = self.content_release
        self.page1.save_revision(self.user)
        self.publisher_api.set_live_content_release(self.content_release.site_code,
                                                    self.content_release.uuid)
        self.page1.content_release = self.content_release
        self.page1.save()

        request = self.factory.post(url, {
            'name1': ['Preview Test model2 name1'],
            'name2': ['Preview Test model2 name2'],
            'body-count': ['2'],
            'body-0-deleted': '',
            'body-0-order': ['0'],
            'body-0-type': ['simple_richtext'],
            'body-0-id': ['dd3b2b0f-a809-4758-a72d-28b570dd26cd'],
            'body-0-value-title': ['Test model1 Title'],
            'body-0-value-body': ['{"blocks":[{"key":"ahkqi","text":"Test model1 Body","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'],
            'body-1-deleted': '',
            'body-1-order': ['1'],
            'body-1-type': ['dynamictestpage_block'],
            'body-1-id': ['e0389402-bac7-4189-a1c7-8c76cb5467ed'],
            'body-1-value': ['3'],
            'super': ['3'],
            'content_release': [self.content_release.id],
            'site_code': [self.content_release.site_code],
        })
        view_response = preview_model(request, 'test_page', 'testmodel', self.test_model.id, 'default')

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(json.loads(view_response.content), {
            'name1': 'Preview Test model2 name1',
            'name2': 'Preview Test model2 name2',
            'body': [{
                'type': 'simple_richtext',
                'id': 'dd3b2b0f-a809-4758-a72d-28b570dd26cd',
                'value': {
                    'title': 'Test model1 Title',
                    'body': '<p>Test model1 Body</p>'},
            }, {
                'type': 'dynamictestpage_block',
                'id': 'e0389402-bac7-4189-a1c7-8c76cb5467ed',
                'value': {
                    'title': 'Test1',
                    'name1': 'Name1'
                },
            }],
            'redirects': []
        })

    def test_release_release_restore(self):
        """ test_release_release_restore """

        # wrong content release id
        url = reverse('wagtailsnapshotpublisher_admin:release_restore', kwargs={
            'release_id': 999,
        })
        request = self.factory.post(url)

        try:
            release_restore(request, 999)
            self.assertFail('''A Http404 exception haven't been raise''')
        except Http404:
            pass

        # release_restore live release
        publish_datetime = timezone.now() - timezone.timedelta(minutes=5)
        self.content_release.status = 1
        self.content_release.publish_datetime = publish_datetime
        self.content_release.save()

        url = reverse('wagtailsnapshotpublisher_admin:release_restore', kwargs={
            'release_id': self.content_release.id,
        })
        request = self.factory.post(url)

        try:
            release_restore(request, self.content_release.id)
            self.assertFail('''A Http404 exception haven't been raise''')
        except Http404:
            pass

        # release_restore
        publish_datetime = timezone.now() - timezone.timedelta(minutes=10)
        content_release2 = WSSPContentRelease.objects.get(id=2)
        content_release2.status = 1
        content_release2.publish_datetime = publish_datetime
        content_release2.save()

        url = reverse('wagtailsnapshotpublisher_admin:release_restore', kwargs={
            'release_id': content_release2.id,
        })
        client_response = self.client.get(url, follow=True)

        self.assertRedirects(
            client_response,
            self.url_release_admin_index,
            status_code=302,
            target_status_code=200,
        )

        restored_release = WSSPContentRelease.objects.get(restored=True)
        self.assertEqual(restored_release.title, '{} - Restored'.format(content_release2.title))

    # def test_get_content_details(self):
    #     """ test_get_content_details """

    # def test_unpublish_recursively_page(self):
    #     """ test_unpublish_recursively_page """

    # def test_unpublish(self):
    #     """ test_unpublish """

    # def test_remove_page(self):
    #     """ test_remove_page """

    # def test_remove_recursively_page(self):
    #     """ test_remove_recursively_page """

    # def test_preview_instance(self):
    #     """ test_preview_instance """
    #     # preview_instance(request, content_app, content_class, content_id, preview_mode='default', load_dynamic_element=True)
