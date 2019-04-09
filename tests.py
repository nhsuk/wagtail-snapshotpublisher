import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from django.contrib.auth.models import User
from django.test import Client

from wagtail.contrib.redirects.models import Redirect
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from djangosnapshotpublisher.models import ReleaseDocument
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

        release_document = ReleaseDocument.objects.get(
            document_key=self.test_model.get_key(),
            content_type=self.test_model.get_name_slug(),
            content_releases=self.content_release,
        )

        self.assertEqual(
            json.loads(release_document.document_json),
            {
                'name1': 'Test Name1',
                'name2': 'Test Name2',
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

        release_document = ReleaseDocument.objects.get(
            document_key=self.test_model.get_key(),
            content_type=self.test_model.get_name_slug(),
            content_releases=self.content_release,
        )

        self.assertEqual(
            json.loads(release_document.document_json),
            {
                'name1': 'Test Name3',
                'name2': 'Test Name4',
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

        self.assertFalse(ReleaseDocument.objects.filter(
                document_key=self.test_model.get_key(),
                content_type=self.test_model.get_name_slug(),
                content_releases=self.content_release,
            ).exists()
        )


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

        simple_richtext_schema = {
            'type' : 'object',
            'required': ['type', 'value'],
            'properties' : {
                'type': {'type' : 'string'},
                'id': {
                    'type' : 'string',
                    'pattern': '^[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}$'
                },
                'value': {
                    'type' : 'object',
                    'required': ['title', 'body'],
                    'properties' : {
                        'title': {'type' : 'string'},
                        'body':{'type' : 'string'},
                    },
                },
            },
        }

        self.test_page_schema = {
            'type' : 'object',
            'required': ['title', 'name1', 'test_related_model', 'child1', 'child3', 'body'],
            'properties' : {
                'title' : {'type' : 'string'},
                'name1' : {'type' : 'string'},
                'test_related_model': {
                    'type' : 'object',
                    'required': ['name'],
                    'properties' : {
                        'name': {'type' : 'string'},
                    },
                },
                'child1': {
                    'type' : 'object',
                    'required': ['name1', 'test_related_model', 'child2'],
                    'properties' : {
                        'name1': {'type' : 'string'},
                        'test_related_model': {
                            'type' : 'object',
                            'required': ['name'],
                            'properties' : {
                                'name': {'type' : 'string'},
                            }
                        },
                        'child2': {
                            'type' : 'object',
                            'required': ['name2'],
                            'properties' : {
                                'name2': {'type' : 'string'},
                            }
                        },
                    },
                },
                'child3':{
                    'type' : 'object',
                    'required': ['name2'],
                    'properties' : {
                        'name2': {'type' : 'string'},
                    },
                },
                'body':{
                    'type' : 'array',
                    "items": [
                        simple_richtext_schema,
                        {
                            'type' : 'object',
                            'required': ['type', 'id', 'value'],
                            'properties' : {
                                'type': {'type' : 'string'},
                                'id': {
                                    'type' : 'string',
                                    'pattern': '^[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}$'
                                },
                                'value': {
                                    'type' : 'object',
                                    'required': ['title', 'body'],
                                    'properties' : {
                                        'title': {'type' : 'string'},
                                        'body':{
                                            'type' : 'array',
                                            'items': simple_richtext_schema,
                                        },
                                    },
                                },
                            },
                        },
                    ]
                },
            },
        }


    def test_create_then_publish(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        release_document = ReleaseDocument.objects.get(
            document_key=self.test_page.get_key(),
            content_type=self.test_page.get_name_slug(),
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

        release_document = ReleaseDocument.objects.get(
            document_key=self.test_page.get_key(),
            content_type=self.test_page.get_name_slug(),
            content_releases=self.content_release,
        )

        document = json.loads(release_document.document_json)
        try:
            validate(instance=document, schema=self.test_page_schema)
        except JsonSchemaValidationError:
            self.fail('Json schema validation failed')

        self.assertEqual(document['title'], 'Title2')
        self.assertEqual(document['name1'], 'Test Name3')
        self.assertEqual(document['child3']['name2'], 'Test Name4')
        self.assertEqual(document['test_related_model']['name'], 'Test Related Name2')
        self.assertEqual(document['body'][0]['type'], 'simple_richtext')
        self.assertEqual(document['body'][0]['value']['title'], 'Simple Rich Text Title3')
        self.assertEqual(document['body'][0]['value']['body'], 'Simple Rich Text Body3')
        self.assertEqual(document['body'][1]['type'], 'block_list')
        self.assertEqual(document['body'][1]['value']['title'], 'Block List Title2')

        self.assertEqual(document['body'][1]['value']['body'][0]['type'], 'simple_richtext')
        self.assertEqual(document['body'][1]['value']['body'][0]['value']['title'], 'Simple Rich Text Title4')
        self.assertEqual(document['body'][1]['value']['body'][0]['value']['body'], 'Simple Rich Text Body4')

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

        self.assertFalse(ReleaseDocument.objects.filter(
                document_key=self.test_page.get_key(),
                content_type=self.test_page.get_name_slug(),
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

        self.assertEqual(ReleaseDocument.objects.count(), 4)

        # Unpublish TestPage recursively to a release
        c = Client()
        response = c.post(
            '/admin/pages/{}/unpublish/{}/recursively/'.format(
                self.test_page.id,
                self.content_release.id,
            ),
        )

        self.assertEqual(ReleaseDocument.objects.count(), 1)

        ReleaseDocument.objects.get(
            document_key=test_page1.get_key(),
            content_type=test_page1.get_name_slug(),
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

        self.assertEqual(ReleaseDocument.objects.filter(
                document_key=self.test_page.get_key(),
                content_type=self.test_page.get_name_slug(),
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

        self.assertEqual(ReleaseDocument.objects.count(), 4)

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
                deleted=True
            ).count(),
            3,
        )
