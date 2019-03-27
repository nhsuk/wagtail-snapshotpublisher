from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import TestModel


class TestModelAdmin(ModelAdmin):
    model = TestModel
    menu_label = 'TestModel'


modeladmin_register(TestModelAdmin)