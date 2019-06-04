"""
.. module:: tests.tests_wagtail_hooks
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from wagtailsnapshotpublisher.models import WSSPContentRelease
from wagtailsnapshotpublisher.wagtail_hooks import ReleaseButtonHelper, ReleaseAdmin


class AdminStreamFieldMetaClassTests(TestCase):
    """ AdminStreamFieldMetaClassTests """

    def setUp(self):
        """ setUp """
        self.admin_user = User.objects.create_superuser('admin', None, 'password')
        self.client = Client()
        self.factory = RequestFactory()

    def test_js_css_loaded(self):
        """ test_js_css_loaded """

        self.client.force_login(self.admin_user)

        # check for create page
        url = reverse('wagtailadmin_pages:add', args=['test_page', 'testpage', 1])
        response = self.client.get(url)

        self.assertContains(
            response,
            '''<link rel="stylesheet" href="/static/wagtailadmin/css/edit-action-release.css">''',
            count=1,
            status_code=200,
            html=True,
        )

        self.assertContains(
            response,
            '''<script src="/static/wagtailadmin/js/edit-action-release.js"></script>''',
            count=1,
            status_code=200,
            html=True,
        )

        # check for update page
        url = reverse('wagtailadmin_pages:edit', args=[2])
        response = self.client.get(url)

        self.assertContains(
            response,
            '''<link rel="stylesheet" href="/static/wagtailadmin/css/edit-action-release.css">''',
            count=1,
            status_code=200,
            html=True,
        )

        self.assertContains(
            response,
            '''<script src="/static/wagtailadmin/js/edit-action-release.js"></script>''',
            count=1,
            status_code=200,
            html=True,
        )

        # check for global css
        url = reverse('wagtailadmin_home')
        response = self.client.get(url)

        self.assertContains(
            response,
            '''<link rel="stylesheet" href="/static/wagtailadmin/css/custom_release.css">''',
            count=1,
            status_code=200,
            html=True,
        )
