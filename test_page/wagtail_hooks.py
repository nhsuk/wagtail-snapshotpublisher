from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import TestModel


class TestModelAdmin(ModelAdmin):
    model = TestModel
    menu_label = 'TestModel'
    edit_template_name = 'modeladmin/edit_with_release.html'


modeladmin_register(TestModelAdmin)