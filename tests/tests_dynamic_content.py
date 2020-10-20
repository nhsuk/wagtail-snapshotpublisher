"""
.. module:: tests.tests_dynamic_content
"""

import os
import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.test.client import RequestFactory
# from django.urls import reverse

from djangosnapshotpublisher.publisher_api import PublisherAPI

from wagtailsnapshotpublisher.models import WSSPContentRelease

from test_page.models import TestPage


class WagtailSnapshotPublisherDynamicContentTests(TestCase):
    """ WagtailSnapshotPublisherDynamicContentTests """

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
        self.page3 = TestPage.objects.get(id=5)
        self.content_release1 = WSSPContentRelease.objects.get(id=1)
        self.content_release2 = WSSPContentRelease.objects.get(id=2)
        self.content_release3 = WSSPContentRelease.objects.get(id=3)
        self.publisher_api = PublisherAPI(api_type='django')
        self.factory = RequestFactory()
        self.client =  Client()
        self.client.force_login(self.user)
        self.page1.content_release = self.content_release1
        self.page1.save_revision(self.user)
        self.page2.content_release = self.content_release1
        self.page2.save_revision(self.user)
        self.page1.publish_to_release(self.page1.content_release, self.content_release1)
        self.publisher_api.set_live_content_release(self.content_release1.site_code, self.content_release1.uuid)
        self.publisher_api.get_live_content_release(self.content_release1.site_code)
        self.content_release1 = WSSPContentRelease.objects.get(id=1)

    # def test_init(self):
    #     self.assertEqual(self.content_release1.release_documents.count(), 4)
    #     self.assertEqual(json.loads(self.content_release1.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1',
    #             'name1': 'Name1',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1',
    #                             'name1': 'Name1'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2',
    #                             'name1': 'Test2 name1'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    # def test_scenario_1(self):
    #     # Release R2 based on R1
    #     self.content_release2.base_release = self.content_release1
    #     self.content_release2.save()

    #     # Update and publish page P2 for R2
    #     self.page2.title = 'Test2.2'
    #     self.page2.name1 = 'Test2 name1.2'
    #     self.page2.name2 = 'Test2 name2.2'
    #     self.page2.content_release = self.content_release2
    #     self.page2.save_revision(self.user)

    #     # Publish release R2
    #     self.page2.publish_to_release(self.page2.content_release, self.content_release2)
    #     self.publisher_api.set_live_content_release(self.content_release2.site_code, self.content_release2.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release2.site_code)

    #     self.assertEqual(self.content_release2.release_documents.count(), 4)
    #     self.assertEqual(json.loads(self.content_release2.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1',
    #             'name1': 'Name1',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1',
    #                             'name1': 'Name1'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2.2',
    #                             'name1': 'Test2 name1.2'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    # def test_scenario_2(self):
    #     # Release R2 based on 'current live release'
    #     self.content_release2.use_current_live_as_base_release = True
    #     self.content_release2.save()

    #     # Update and publish page P2
    #     self.page2.title = 'Test2.2'
    #     self.page2.name1 = 'Test2 name1.2'
    #     self.page2.name2 = 'Test2 name2.2'
    #     self.page2.content_release = self.content_release2
    #     self.page2.save_revision(self.user)
    #     self.page2.publish_to_release(self.page2.content_release, self.content_release2)

    #     # Release R3 based on 'R1'
    #     self.content_release3.base_release = self.content_release1
    #     self.content_release3.save()

    #     # Update and publish page P2
    #     self.page2.title = 'Test2.3'
    #     self.page2.name1 = 'Test2 name1.3'
    #     self.page2.name2 = 'Test2 name2.3'
    #     self.page2.content_release = self.content_release3
    #     self.page2.save_revision(self.user)

    #     # Update and publish page P1
    #     self.page1.title = 'Test1.2'
    #     self.page1.name1 = 'Name1.2'
    #     self.page1.name2 = 'Name2.2'
    #     self.page1.content_release = self.content_release3
    #     self.page1.save_revision(self.user)
    #     self.page1.publish_to_release(self.page1.content_release, self.content_release3)

    #     # Publish release R3
    #     self.publisher_api.set_live_content_release(self.content_release3.site_code, self.content_release3.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release3.site_code)
    #     self.assertEqual(self.content_release3.release_documents.count(), 4)
    #     self.assertEqual(json.loads(self.content_release3.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1.2',
    #             'name1': 'Name1.2',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1.2',
    #                             'name1': 'Name1.2'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2.3',
    #                             'name1': 'Test2 name1.3'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    #     # Publish release R2
    #     self.publisher_api.set_live_content_release(self.content_release2.site_code, self.content_release2.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release2.site_code)
    #     self.assertEqual(self.content_release2.release_documents.count(), 4)
    #     self.assertEqual(json.loads(self.content_release2.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1.2',
    #             'name1': 'Name1.2',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1.2',
    #                             'name1': 'Name1.2'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2.2',
    #                             'name1': 'Test2 name1.2'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    # def test_scenario_3(self):
    #     # Release R2 based on 'current live release'
    #     self.content_release2.use_current_live_as_base_release = True
    #     self.content_release2.save()

    #     # Update and publish page P2
    #     self.page2.title = 'Test2.2'
    #     self.page2.name1 = 'Test2 name1.2'
    #     self.page2.name2 = 'Test2 name2.2'
    #     self.page2.content_release = self.content_release2
    #     self.page2.save_revision(self.user)
    #     self.page2.publish_to_release(self.page2.content_release, self.content_release2)

    #     # Release R3 based on 'R1'
    #     self.content_release3.base_release = self.content_release1
    #     self.content_release3.save()

    #     # Update and publish new page P3 to R2
    #     self.page3.content_release = self.content_release2
    #     self.page3.save_revision(self.user)
    #     self.page3.publish_to_release(self.page3.content_release, self.content_release2)

    #     # Update and publish page P2 to R3
    #     self.page2.title = 'Test2.3'
    #     self.page2.name1 = 'Test2 name1.3'
    #     self.page2.name2 = 'Test2 name2.3'
    #     self.page2.content_release = self.content_release3
    #     self.page2.save_revision(self.user)
    #     self.page2.publish_to_release(self.page2.content_release, self.content_release3)

    #    # Update and publish page P1 to R3
    #     self.page1.title = 'Test1.2'
    #     self.page1.name1 = 'Test1 name1.2'
    #     self.page1.name2 = 'Test1 name2.2'
    #     self.page1.body = json.dumps([
    #         {
    #             'type': 'simple_richtext',
    #             'value': {
    #                 'title': 'Title1',
    #                 'body': '<p>Body1</p>'
    #             },
    #             'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #         }, {
    #             'type': 'dynamictestpage_block',
    #             'value': 3,
    #             'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #         }, {
    #             'type': 'dynamictestpage_block',
    #             'value': 4,
    #             'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #         }, {
    #             'type': 'dynamictestpage_block',
    #             'value': 5,
    #             'id': '26ab3837-c224-4b28-bd29-24e0b38c5793'
    #         }
    #     ])
    #     self.page1.content_release = self.content_release3
    #     self.page1.save_revision(self.user)
    #     self.page1.publish_to_release(self.page1.content_release, self.content_release3)

    #     # Publish release R3
    #     self.publisher_api.set_live_content_release(self.content_release3.site_code, self.content_release3.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release3.site_code)
    #     self.assertEqual(self.content_release3.release_documents.count(), 4)
    #     self.assertEqual(json.loads(self.content_release3.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1.2',
    #             'name1': 'Test1 name1.2',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1.2',
    #                             'name1': 'Test1 name1.2'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2.3',
    #                             'name1': 'Test2 name1.3'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 5,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c5793'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    #     # Publish release R2
    #     self.publisher_api.set_live_content_release(self.content_release2.site_code, self.content_release2.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release2.site_code)
    #     self.assertEqual(self.content_release2.release_documents.count(), 6)
    #     self.assertEqual(json.loads(self.content_release2.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1.2',
    #             'name1': 'Test1 name1.2',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1.2',
    #                             'name1': 'Test1 name1.2'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2.2',
    #                             'name1': 'Test2 name1.2'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 5,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test3',
    #                             'name1': 'Test3 name1'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c5793'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    # def test_scenario_4(self):
    #     # Release R2 based on 'current live release'
    #     self.content_release2.use_current_live_as_base_release = True
    #     self.content_release2.save()

    #     # Update and publish page P2
    #     self.page2.title = 'Test2.2'
    #     self.page2.name1 = 'Test2 name1.2'
    #     self.page2.name2 = 'Test2 name2.2'
    #     self.page2.content_release = self.content_release2
    #     self.page2.save_revision(self.user)
    #     self.page2.publish_to_release(self.page2.content_release, self.content_release2)

    #     # Release R3 based on 'R1'
    #     self.content_release3.base_release = self.content_release1
    #     self.content_release3.save()

    #     # Update and publish new page P3 to R2
    #     self.page3.content_release = self.content_release2
    #     self.page3.save_revision(self.user)
    #     self.page3.publish_to_release(self.page3.content_release, self.content_release2)

    #     # Update and publish page P2 to R3
    #     self.page2.title = 'Test2.3'
    #     self.page2.name1 = 'Test2 name1.3'
    #     self.page2.name2 = 'Test2 name2.3'
    #     self.page2.content_release = self.content_release3
    #     self.page2.save_revision(self.user)
    #     self.page2.publish_to_release(self.page2.content_release, self.content_release3)

    #    # Update and publish page P1 to R3
    #     self.page1.title = 'Test1.2'
    #     self.page1.name1 = 'Test1 name1.2'
    #     self.page1.name2 = 'Test1 name2.2'
    #     self.page1.body = json.dumps([
    #         {
    #             'type': 'simple_richtext',
    #             'value': {
    #                 'title': 'Title1',
    #                 'body': '<p>Body1</p>'
    #             },
    #             'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #         }, {
    #             'type': 'dynamictestpage_block',
    #             'value': 3,
    #             'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #         }, {
    #             'type': 'dynamictestpage_block',
    #             'value': 4,
    #             'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #         }, {
    #             'type': 'dynamictestpage_block',
    #             'value': 5,
    #             'id': '26ab3837-c224-4b28-bd29-24e0b38c5793'
    #         }
    #     ])
    #     self.page1.content_release = self.content_release3
    #     self.page1.save_revision(self.user)
    #     self.page1.publish_to_release(self.page1.content_release, self.content_release3)

    #     # Remove page P2 from R3
    #     self.page2.unpublish_or_delete_from_release(self.content_release3.id, False, True)

    #     # Publish release R3
    #     self.publisher_api.set_live_content_release(self.content_release3.site_code, self.content_release3.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release3.site_code)
    #     self.assertEqual(self.content_release3.release_documents.count(), 4)
    #     self.assertEqual(json.loads(self.content_release3.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1.2',
    #             'name1': 'Test1 name1.2',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1.2',
    #                             'name1': 'Test1 name1.2'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 5,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c5793'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )

    #     # Publish release R2
    #     self.publisher_api.set_live_content_release(self.content_release2.site_code, self.content_release2.uuid)
    #     self.publisher_api.get_live_content_release(self.content_release2.site_code)
    #     self.assertEqual(self.content_release2.release_documents.count(), 6)
    #     self.assertEqual(json.loads(self.content_release2.release_documents.get(document_key=3, content_type='page').document_json),
    #         {
    #             'title': 'Test1.2',
    #             'name1': 'Test1 name1.2',
    #             'body': [
    #                 {
    #                     'type': 'simple_richtext',
    #                     'value': {
    #                         'title': 'Title1',
    #                         'body': '<p>Body1</p>'
    #                     },
    #                     'id': 'ba2832a9-f580-424f-bee8-f081a3eb7b86'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 3,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test1.2',
    #                             'name1': 'Test1 name1.2'
    #                         }
    #                     },
    #                     'id': '4b6285fb-3fa1-4f9d-9b35-7250b28f81f8'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 4,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test2.2',
    #                             'name1': 'Test2 name1.2'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c0981'
    #                 }, {
    #                     'type': 'dynamictestpage_block',
    #                     'value': {
    #                         'ref': {
    #                             'id': 5,
    #                             'serializer': 'cover',
    #                             'dynamic': True,
    #                             'app': 'test_page',
    #                             'class': 'TestPage'
    #                         },
    #                         'data': {
    #                             'title': 'Test3',
    #                             'name1': 'Test3 name1'
    #                         }
    #                     },
    #                     'id': '26ab3837-c224-4b28-bd29-24e0b38c5793'
    #                 }
    #             ],
    #             'test_related_model': [1]
    #         }
    #     )
