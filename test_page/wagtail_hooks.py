from wagtail.contrib.modeladmin.options import modeladmin_register

from wagtailsnapshotpublisher.wagtail_hooks import ModelAdminWithRelease

from .models import TestModel


class TestModelAdmin(ModelAdminWithRelease):
    model = TestModel
    menu_label = 'TestModel'
    edit_template_name = 'modeladmin/edit_with_release.html'


modeladmin_register(TestModelAdmin)