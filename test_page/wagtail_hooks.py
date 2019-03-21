# from django.templatetags.static import static
# from django.urls import resolve
# from django.utils.html import format_html, format_html_join
# from django.utils.translation import ugettext_lazy as _

# from wagtail.admin.action_menu import ActionMenuItem
# from wagtail.admin.edit_handlers import FieldPanel
# from wagtail.contrib.forms.models import AbstractForm
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
# from wagtail.core import hooks

from .models import TestModel


class TestModelAdmin(ModelAdmin):
    model = TestModel
    menu_label = 'SiteSetting'
    # menu_icon = 'date'
    # menu_order = 900 

    # list_display = ('title', 'uuid', 'status', 'publish_datetime')
    # search_fields = ('title',)

modeladmin_register(TestModelAdmin)
