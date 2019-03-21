import json

from django.contrib.auth.models import User
from django.test import Client

from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from djangosnapshotpublisher.models import ReleaseDocument
from wagtailsnapshotpublisher.models import WSSPContentRelease

from test_page.models import TestModel, TestPage


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

        # Create TestModel
        self.test_model = TestModel(
            name='SiteSetting1',
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
                'name': 'SiteSetting1',
            }
        )

    def test_update_then_publish(self):
        # Publish TestModel to a release
        c = Client()
        response = c.post(
            '/admin/test_page/testmodel/edit/{}/'.format(self.test_model.id),
        )

        self.assertEqual(response.status_code, 302)

        # Update TestModel
        self.test_model.name = 'SiteSetting2'
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
                'name': 'SiteSetting2',
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
        homepage = Page.objects.get(id=1)

        self.test_page = TestPage(
            title='Title1',
            content_release=self.content_release,
        )
        homepage.add_child(instance=self.test_page)
        self.test_page.save()


    def test_create_then_publish(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        release_document = ReleaseDocument.objects.get(
            document_key=self.test_page.get_key(),
            content_type=self.test_page.get_name_slug(),
            content_releases=self.content_release,
        )

        self.assertEqual(
            json.loads(release_document.document_json),
            {
                'title': 'Title1',
            }
        )

    def test_update_then_publish(self):
        # Publish TestPage to a release
        self.test_page.save_revision(self.user)

        # Update TestPage
        self.test_page.content_release = self.content_release
        self.test_page.title = 'Title2'
        self.test_page.save()

        # Republish TestPage to a release
        self.test_page.save_revision(self.user)

        release_document = ReleaseDocument.objects.get(
            document_key=self.test_page.get_key(),
            content_type=self.test_page.get_name_slug(),
            content_releases=self.content_release,
        )

        self.assertEqual(
            json.loads(release_document.document_json),
            {
                'title': 'Title2',
            }
        )

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