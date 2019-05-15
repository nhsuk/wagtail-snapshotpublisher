import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from wagtail.contrib.redirects.models import Redirect
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from djangosnapshotpublisher.models import ReleaseDocument
from djangosnapshotpublisher.publisher_api import PublisherAPI
from wagtailsnapshotpublisher.models import WSSPContentRelease

from test_page.models import TestModel, TestPage, TestRelatedModel


class ModelWithReleaseTests(WagtailPageTests):

    def setUp(self):
        """ setUp """

        # Create ContentRelease
        self.content_release = WSSPContentRelease(
            title='release1',
            site_code='site1',
            version='0.1',
            status=0,
        )
        self.content_release.save()

        redirect = Redirect(
            old_path='/test',
            is_permanent=True,
            redirect_link='/test2',
        )
        redirect.save()

        # Create TestModel
        self.test_model = TestModel(
            name1='Test Name1',
            name2='Test Name2',
            content_release=self.content_release,
        )
        self.test_model.save()

    def test_create_then_publish(self):
        # Publish TestModel to a release
        c = Client()
        response = c.post(
            '/admin/test_page/testmodel/edit/{}/'.format(self.test_model.id),
        )

        self.assertEqual(response.status_code, 302)

        serializers = self.test_model.get_serializers()
        release_document = ReleaseDocument.objects.get(
            document_key=serializers['default']['key'],
            content_type=serializers['default']['type'],
            content_releases=self.content_release,
        )

        self.assertEqual(
            json.loads(release_document.document_json),
            {
                'name1': 'Test Name1',
                'name2': 'Test Name2',
                'content_release':  self.content_release.id,
                'redirects': [{
                    'old_path': '/test',
                    'is_permanent': True,
                    'redirect_link': '/test2',
                }]
            }
        )

    def test_update_then_publish(self):
        # Publish TestModel to a release
        c = Client()
        response = c.post(
            '/admin/test_page/testmodel/edit/{}/'.format(self.test_model.id),
        )

        self.assertEqual(response.status_code, 302)

        # Add redirection
        redirect = Redirect(
            old_path='/test3',
            is_permanent=False,
            redirect_link='/test4',
        )
        redirect.save()

        # Update TestModel
        self.test_model.name1 = 'Test Name3'
        self.test_model.name2 = 'Test Name4'
        self.test_model.save()

        # Republish TestModel to a release
        c = Client()
        response = c.post(
            '/admin/test_page/testmodel/edit/{}/'.format(self.test_model.id),
        )
        self.assertEqual(response.status_code, 302)

        serializers = self.test_model.get_serializers()
        release_document = ReleaseDocument.objects.get(
            document_key=serializers['default']['key'],
            content_type=serializers['default']['type'],
            content_releases=self.content_release,
        )

        self.assertEqual(
            json.loads(release_document.document_json),
            {
                'name1': 'Test Name3',
                'name2': 'Test Name4',
                'content_release':  self.content_release.id,
                'redirects': [{
                    'old_path': '/test',
                    'is_permanent': True,
                    'redirect_link': '/test2',
                }, {
                    'old_path': '/test3',
                    'is_permanent': False,
                    'redirect_link': '/test4',
                }]
            }
        )

    def test_update_unpublish(self):
        # Publish TestModel to a release
        c = Client()
        response = c.post(
            '/admin/test_page/testmodel/edit/{}/'.format(self.test_model.id),
        )

        self.assertEqual(response.status_code, 302)

        # Unpublish TestModel to a release
        c = Client()
        response = c.post(
            '/admin/test_page/testmodel/unpublish/{}/{}/'.format(
                self.test_model.id,
                self.content_release.id,
            ),
        )

        self.assertEqual(response.status_code, 302)

        serializers = self.test_model.get_serializers()
        self.assertFalse(ReleaseDocument.objects.filter(
                document_key=serializers['default']['key'],
                content_type=serializers['default']['type'],
                content_releases=self.content_release,
            ).exists()
        )
        self.assertFalse(ReleaseDocument.objects.filter(
                document_key=serializers['cover']['key'],
                content_type=serializers['cover']['type'],
                content_releases=self.content_release,
            ).exists()
        )
    
    def test_define_version(self):
        
        # Create ContentRelease Major Version
        content_release1 = WSSPContentRelease(
            title='release1',
            site_code='site1',
            version_type=0,
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(days=10),
        )
        content_release1.save()
        content_release1 = WSSPContentRelease.objects.get(id=content_release1.id)
        self.assertEqual(content_release1.version, '1.0')

        # Create ContentRelease Minor Version
        content_release2 = WSSPContentRelease(
            title='release2',
            site_code='site1',
            version_type=1,
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(days=5),
        )
        content_release2.save()
        content_release2 = WSSPContentRelease.objects.get(id=content_release2.id)
        self.assertEqual(content_release2.version, '1.1')

        # Create ContentRelease Patch Version
        content_release3 = WSSPContentRelease(
            title='release3',
            site_code='site1',
            version_type=0,
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(days=11),
        )
        content_release3.save()

        # content_release1 = 2.0
        # content_release2 = 2.1
        # content_release3 = 1.0
        content_release1 = WSSPContentRelease.objects.get(id=content_release1.id)
        self.assertEqual(content_release1.version, '2.0')
        content_release2 = WSSPContentRelease.objects.get(id=content_release2.id)
        self.assertEqual(content_release2.version, '2.1')
        content_release3 = WSSPContentRelease.objects.get(id=content_release3.id)
        self.assertEqual(content_release3.version, '1.0')

        # Create ContentRelease Patch Version
        content_release4 = WSSPContentRelease(
            title='release4',
            site_code='site1',
            version_type=1,
            status=1,
            publish_datetime=timezone.now() - timezone.timedelta(days=6),
        )
        content_release4.save()

        # content_release1 = 2.0
        # content_release2 = 2.2
        # content_release3 = 1.0
        # content_release4 = 2.1
        content_release1 = WSSPContentRelease.objects.get(id=content_release1.id)
        self.assertEqual(content_release1.version, '2.0')
        content_release2 = WSSPContentRelease.objects.get(id=content_release2.id)
        self.assertEqual(content_release2.version, '2.2')
        content_release3 = WSSPContentRelease.objects.get(id=content_release3.id)
        self.assertEqual(content_release3.version, '1.0')
        content_release4 = WSSPContentRelease.objects.get(id=content_release4.id)
        self.assertEqual(content_release4.version, '2.1')


class PageWithReleaseTests(WagtailPageTests):

    def setUp(self):
        """ setUp """

        # Get User
        self.user = User.objects.create_user(
            username='test',
            email='test.test@test.test',
            password='testpassword'
        )

        # Create ContentRelease
        self.content_release = WSSPContentRelease(
            title='release1',
            site_code='site1',
            version='0.1',
            status=0,
        )
        self.content_release.save()

        # Create TestPage
        self.homepage = Page.objects.get(id=1)

        self.test_page = TestPage(
            title='Title1',
            name1='Test Name1',
            name2='Test Name2',
            body=json.dumps([
                {
                    'type': 'simple_richtext', 'value': {
                        'title': 'Simple Rich Text Title',
                        'body': 'Simple Rich Text Body',
                    }
                },
                {
                    'type': 'block_list', 'value': {
                        'title': 'Block List Title',
                        'body': [
                            {
                                'type': 'simple_richtext', 'value': {
                                    'title': 'Simple Rich Text Title2',
                                    'body': 'Simple Rich Text Body2',
                                }
                            }
                        ]
                    }
                },
            ]),
            content_release=self.content_release,
        )
        self.homepage.add_child(instance=self.test_page)
        self.test_page.save()

        # Create TestRelatedModel
        self.test_related_model = TestRelatedModel(
            test_page=self.test_page,
            name='Test Related Name1',
        )
        self.test_related_model.save()

        self.test_page_schema = {
            'type' : 'object',
            'required': ['title', 'name1', 'test_related_model', 'body'],
            'properties' : {
                'title' : {'type' : 'string'},
                'name1' : {'type' : 'string'},
                'test_related_model': {
                    'type' : 'array',
                },
                'body':{
                    'type' : 'array',
                },
            },
        }


    def test_create_then_publish(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        serializers = self.test_page.get_serializers()
        release_document = ReleaseDocument.objects.get(
            document_key=serializers['default']['key'],
            content_type=serializers['default']['type'],
            content_releases=self.content_release,
        )

        try:
            validate(instance=json.loads(release_document.document_json), schema=self.test_page_schema)
        except JsonSchemaValidationError:
            self.fail('Json schema validation failed')

    def test_update_then_publish(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        # Update TestPage
        self.test_page.content_release = self.content_release
        self.test_page.title = 'Title2'
        self.test_page.name1 = 'Test Name3'
        self.test_page.name2 = 'Test Name4'
        self.test_page.body=json.dumps([
            {
                'type': 'simple_richtext', 'value': {
                    'title': 'Simple Rich Text Title3',
                    'body': 'Simple Rich Text Body3',
                }
            },
            {
                'type': 'block_list', 'value': {
                    'title': 'Block List Title2',
                    'body': [
                        {
                            'type': 'simple_richtext', 'value': {
                                'title': 'Simple Rich Text Title4',
                                'body': 'Simple Rich Text Body4',
                            }
                        }
                    ]
                }
            },
        ])
        self.test_page.save()
        

        # Update TestRelatedModel
        self.test_related_model.name = 'Test Related Name2'
        self.test_related_model.save()

        # Republish TestPage to a release
        self.test_page.save_revision(self.user)

        serializers = self.test_page.get_serializers()
        release_document = ReleaseDocument.objects.get(
            document_key=serializers['default']['key'],
            content_type=serializers['default']['type'],
            content_releases=self.content_release,
        )

        document = json.loads(release_document.document_json)
        try:
            validate(instance=document, schema=self.test_page_schema)
        except JsonSchemaValidationError:
            self.fail('Json schema validation failed')

        self.assertEqual(document['title'], 'Title2')
        self.assertEqual(document['name1'], 'Test Name3')

    def test_update_unpublish(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        # Unpublish TestPage to a release
        c = Client()
        response = c.post(
            '/admin/pages/{}/unpublish/{}/'.format(
                self.test_page.id,
                self.content_release.id,
            ),
        )

        self.assertEqual(response.status_code, 302)


        serializers = self.test_page.get_serializers()
        self.assertFalse(ReleaseDocument.objects.filter(
                document_key=serializers['default']['key'],
                content_type=serializers['default']['type'],
                content_releases=self.content_release,
            ).exists()
        )
        self.assertFalse(ReleaseDocument.objects.filter(
                document_key=serializers['cover']['key'],
                content_type=serializers['cover']['type'],
                content_releases=self.content_release,
            ).exists()
        )


    def test_unpublish_recursively(self):
        # -homepage
        #  |-test_page
        #    |-test_page2
        #      |-test_page3
        #  |-test_page1
        test_page1 = self.test_page.copy(False, self.homepage, {'slug': 'test_page1'})
        test_page2 = self.test_page.copy(False, self.test_page)
        test_page3 = self.test_page.copy(False, test_page2)

        self.test_page.save_revision(self.user)
        test_page1.save_revision(self.user)
        test_page2.save_revision(self.user)
        test_page3.save_revision(self.user)

        self.assertEqual(ReleaseDocument.objects.filter(content_type='page').count(), 4)
        self.assertEqual(ReleaseDocument.objects.filter(content_type='cover').count(), 4)

        # Unpublish TestPage recursively to a release
        c = Client()
        response = c.post(
            '/admin/pages/{}/unpublish/{}/recursively/'.format(
                self.test_page.id,
                self.content_release.id,
            ),
        )

        self.assertEqual(ReleaseDocument.objects.filter(content_type='page').count(), 1)
        self.assertEqual(ReleaseDocument.objects.filter(content_type='cover').count(), 1)

        serializers = test_page1.get_serializers()
        release_document = ReleaseDocument.objects.get(
            document_key=serializers['default']['key'],
            content_type=serializers['default']['type'],
            content_releases=self.content_release,
        )

    def test_update_remove(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        # Remove TestPage to a release
        c = Client()
        response = c.post(
            '/admin/pages/{}/remove/{}/'.format(
                self.test_page.id,
                self.content_release.id,
            ),
        )

        self.assertEqual(response.status_code, 302)

        serializers = self.test_page.get_serializers()
        self.assertEqual(ReleaseDocument.objects.filter(
                document_key=serializers['default']['key'],
                content_type=serializers['default']['type'],
                content_releases=self.content_release,
                deleted=True
            ).count(),
            1,
        )
        self.assertEqual(ReleaseDocument.objects.filter(
                document_key=serializers['default']['key'],
                content_type=serializers['default']['type'],
                content_releases=self.content_release,
                deleted=True
            ).count(),
            1,
        )

    def test_remove_recursively(self):
        # -homepage
        #  |-test_page
        #    |-test_page2
        #      |-test_page3
        #  |-test_page1
        test_page1 = self.test_page.copy(False, self.homepage, {'slug': 'test_page1'})
        test_page2 = self.test_page.copy(False, self.test_page)
        test_page3 = self.test_page.copy(False, test_page2)

        self.test_page.save_revision(self.user)
        test_page1.save_revision(self.user)
        test_page2.save_revision(self.user)
        test_page3.save_revision(self.user)

        self.assertEqual(ReleaseDocument.objects.filter(content_type='page').count(), 4)
        self.assertEqual(ReleaseDocument.objects.filter(content_type='cover').count(), 4)

        # Remove TestPage recursively to a release
        c = Client()
        response = c.post(
            '/admin/pages/{}/remove/{}/recursively/'.format(
                self.test_page.id,
                self.content_release.id,
            ),
        )

        self.assertEqual(ReleaseDocument.objects.filter(
                content_releases=self.content_release,
                deleted=True,
                content_type='page',
            ).count(),
            3,
        )

        self.assertEqual(ReleaseDocument.objects.filter(
                content_releases=self.content_release,
                deleted=True,
                content_type='cover',
            ).count(),
            3,
        )

    def test_restore_release(self):
        self.test_page.content_release = self.content_release
        revision_test_page1_r1 = self.test_page.save_revision(self.user)

        test_page2 = self.test_page.copy(False, self.test_page, {'title': 'Title2'})
        test_page2.content_release = self.content_release
        revision_test_page2_r1 = test_page2.save_revision(self.user)

        publisher_api = PublisherAPI()
        publisher_api.set_live_content_release(self.content_release.site_code, self.content_release.uuid)

        # Create content_release2
        content_release2 = WSSPContentRelease(
            title='release2',
            site_code='site1',
            version='0.2',
            status=0,
        )
        content_release2.save()

        test_page3 = self.test_page.copy(False, self.test_page, {'slug': 'test_page3', 'title': 'Title3'})
        test_page3.content_release = content_release2
        revision_test_page3_r2 = test_page3.save_revision(self.user)

        test_page2.content_release = content_release2
        revision_test_page2_r2 = test_page2.save_revision(self.user)

        publisher_api = PublisherAPI()
        publisher_api.set_live_content_release(content_release2.site_code, content_release2.uuid)

        response = publisher_api.compare_content_releases(content_release2.site_code, content_release2.uuid, self.content_release.uuid)
        comparison = response['content']

        self.assertEqual(comparison, [
                {
                    'document_key': str(test_page3.id),
                    'content_type': 'cover',
                    'diff': 'Added',
                     'parameters': {'revision_id': str(revision_test_page3_r2.id)}
                }, {
                    'document_key': str(test_page3.id),
                    'content_type': 'page',
                    'diff': 'Added',
                    'parameters': {'revision_id': str(revision_test_page3_r2.id)}
                }, {
                    'document_key': str(test_page2.id),
                    'content_type': 'cover',
                    'diff': 'Changed',
                    'parameters': {
                        'release_from': {'revision_id': str(revision_test_page2_r2.id)},
                        'release_compare_to': {'revision_id': str(revision_test_page2_r1.id)}
                    }
                }, {
                    'document_key': str(test_page2.id),
                    'content_type': 'page',
                    'diff': 'Changed',
                    'parameters': {
                        'release_from': {'revision_id': str(revision_test_page2_r2.id)},
                        'release_compare_to': {'revision_id': str(revision_test_page2_r1.id)}
                    }
                }, {
                    'document_key': str(self.test_page.id),
                    'content_type': 'cover',
                    'diff': 'Removed',
                    'parameters': {'revision_id': str(revision_test_page1_r1.id)}
                }, {
                    'document_key': str(self.test_page.id),
                    'content_type': 'page',
                    'diff': 'Removed',
                    'parameters': {'revision_id': str(revision_test_page1_r1.id)}
                }
            ]
        )

        # Restore content_release
        c = Client()
        response = c.post(
            '/admin/wagtailsnapshotpublisher/wsspcontentrelease/restore/{}/'.format(
                self.content_release.id,
            ),
        )

        restored_release = WSSPContentRelease.objects.get(
            site_code='site1',
            restored=True,
        )

        response = publisher_api.compare_content_releases(restored_release.site_code, restored_release.uuid, content_release2.uuid)
        comparison = response['content']

        self.assertEqual(comparison, [
            {
                'document_key': str(self.test_page.id),
                'content_type': 'cover',
                'diff': 'Added',
                'parameters': {'revision_id': str(revision_test_page1_r1.id)}
            }, {
                'document_key': str(self.test_page.id),
                'content_type': 'page',
                'diff': 'Added',
                'parameters': {'revision_id': str(revision_test_page1_r1.id)}
            }, {
                'document_key': str(test_page2.id),
                'content_type': 'cover',
                'diff': 'Changed',
                'parameters': {'release_from': {'revision_id': str(revision_test_page2_r1.id)},
                'release_compare_to': {'revision_id': str(revision_test_page2_r2.id)}}
            }, {
                'document_key': str(test_page2.id),
                'content_type': 'page',
                'diff': 'Changed',
                'parameters': {'release_from': {'revision_id': str(revision_test_page2_r1.id)},
                'release_compare_to': {'revision_id': str(revision_test_page2_r2.id)}}
            }, {
                'document_key': str(test_page3.id),
                'content_type': 'cover',
                'diff': 'Removed',
                'parameters': {'revision_id': str(revision_test_page3_r2.id)}
            }, {
                'document_key': str(test_page3.id),
                'content_type': 'page',
                'diff': 'Removed',
                'parameters': {'revision_id': str(revision_test_page3_r2.id)}
            }
        ]
    )
