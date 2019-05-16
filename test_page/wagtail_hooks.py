from wagtail.contrib.modeladmin.options import modeladmin_register

from wagtailsnapshotpublisher.wagtail_hooks import ModelAdminWithRelease

from .models import TestModel, SiteSettings


class TestModelAdmin(ModelAdminWithRelease):
    model = TestModel
    menu_label = 'TestModel'
    edit_template_name = 'modeladmin/edit_with_release.html'


modeladmin_register(TestModelAdmin)


class SiteSettingsAdmin(ModelAdminWithRelease):
    model = SiteSettings
    menu_label = 'SiteSettings'
    edit_template_name = 'modeladmin/edit_with_release.html'
    add_to_settings_menu = True


modeladmin_register(SiteSettingsAdmin)
