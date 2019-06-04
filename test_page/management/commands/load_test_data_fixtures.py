import os
import sys

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from wagtail.core.models import Page

from wagtailsnapshotpublisher.models import WithRelease

from test_page.models import SiteSettings, update_site_code_widget_for_content_release


GREEN = '\033[0;32m'
RESET = '\033[0;0m'


class Command(BaseCommand):
    """ Command """
    help = 'Load Test Data Fixture'

    def add_arguments(self, parser):
        """ add_arguments """
        # no-output (optional) arguments
        parser.add_argument(
            '--no-output',
            action='store_true',
        )

    def handle(self, *args, **options):
        """ handle """
        self.no_output = options['no_output']

        User = get_user_model()
        username = os.environ.get('CMS_SUPERUSER_USERNAME', 'superadmin')
        if not User.objects.filter(username=username).exists():
            # Create superuser
            self.custom_print('1 - Create superuser')
            password = os.environ.get('CMS_SUPERUSER_PASSWORD', 'superpassword')
            superuser = User.objects.create_superuser(username, None, password, id=8)
            self.custom_print(' DONE\n', GREEN)

            # Remove Welcome Wagtail page
            self.custom_print('2 - Remove Welcome Wagtail page')
            try:
                Page.objects.get(title='Welcome to your new Wagtail site!').delete()
            except Page.DoesNotExist:
                pass
            self.custom_print(' DONE\n', GREEN)

            # Load Fixtures
            self.custom_print('3 - Load Main Fixtures\n')
            load_test_data_cmd = ['loaddata', './fixtures/test-data.json']
            if self.no_output:
                load_test_data_cmd.append('-v0')
            call_command(*load_test_data_cmd)
            self.custom_print('DONE\n', GREEN)

            # Update SiteSettings
            self.custom_print('4 - Update SiteSettings')
            update_site_code_widget_for_content_release(SiteSettings, None)
            self.custom_print(' DONE\n', GREEN)

            # Load Fixtures
            self.custom_print('5 - Load Release Fixtures\n')
            load_test_release_data_cmd = ['loaddata', './fixtures/test-data-release.json']
            if self.no_output:
                load_test_release_data_cmd.append('-v0')
            call_command(*load_test_release_data_cmd)
            self.custom_print(' DONE\n', GREEN)

    def custom_print(self, message, color=None):
        if not self.no_output:
            if color is not None:
                sys.stdout.write(color)
            sys.stdout.write(message)
            if color is not None:
                sys.stdout.write(RESET)
